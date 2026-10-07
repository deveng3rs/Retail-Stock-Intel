"""Fixed-rule baseline: what a store does today without the system.

Rule: apply a flat markdown once N days remain; no transfers; unsold units are written off.
Standard library only. Run from the project root (after generate_seed.py):
    python3 agents/baseline.py

IMPORTANT: ELASTICITY and the other numbers below are ASSUMPTIONS for a simulation, not measured values.
Real results will differ from the example numbers in contracts/*.json, which are placeholders.
"""
import csv
import os
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "out"
TODAY = date(2026, 10, 7)

MARKDOWN_PCT = 30            # fixed discount
MARKDOWN_STARTS_DAYS_LEFT = 3
ELASTICITY = float(os.environ.get("ELASTICITY", 2.5))  # demand multiplier = 1 + ELASTICITY * discount (ASSUMPTION)
DEMAND_WINDOW_DAYS = 14      # naive forecast = average of the last 14 days
AT_RISK_UNSOLD_SHARE = 0.10  # a batch is at risk if >= 10% of stock would expire unsold


def read(name):
    with open(OUT / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def naive_daily_demand(sales, store_id, sku_id):
    rows = [r for r in sales if r["store_id"] == store_id and r["sku_id"] == sku_id]
    rows.sort(key=lambda r: r["sale_date"])
    last = rows[-DEMAND_WINDOW_DAYS:]
    return sum(int(r["units_sold"]) for r in last) / max(len(last), 1)


def simulate(stock, demand, price, days_to_expiry, markdown_pct, markdown_days_left):
    """Return (units_sold, revenue). Demand is per day; markdown applies when days_left <= markdown_days_left."""
    stock_left, sold, revenue = float(stock), 0.0, 0.0
    for i in range(days_to_expiry):
        days_left = days_to_expiry - i
        disc = markdown_pct / 100 if (markdown_pct and days_left <= markdown_days_left) else 0.0
        units = min(stock_left, demand * (1 + ELASTICITY * disc))
        stock_left -= units
        sold += units
        revenue += units * price * (1 - disc)
    return sold, revenue


def main():
    sales, skus, batches = read("daily_sales.csv"), read("skus.csv"), read("batches.csv")
    price = {s["sku_id"]: float(s["unit_price_inr"]) for s in skus}
    name = {s["sku_id"]: s["sku_name"] for s in skus}

    out_rows, tot_hold, tot_base, at_risk, worse = [], 0.0, 0.0, 0, 0
    for b in batches:
        days = (date.fromisoformat(b["expiry_date"]) - TODAY).days
        if days <= 0:
            continue
        stock = int(b["quantity_on_hand"])
        demand = naive_daily_demand(sales, b["store_id"], b["sku_id"])
        p = price[b["sku_id"]]
        hold_units, hold_rev = simulate(stock, demand, p, days, 0, 0)
        base_units, base_rev = simulate(stock, demand, p, days, MARKDOWN_PCT, MARKDOWN_STARTS_DAYS_LEFT)
        unsold_hold = stock - hold_units
        is_risk = unsold_hold / stock >= AT_RISK_UNSOLD_SHARE
        if is_risk:
            at_risk += 1
            tot_hold += hold_rev
            tot_base += base_rev
            if base_rev < hold_rev:
                worse += 1
        out_rows.append({
            "batch_id": b["batch_id"], "store_id": b["store_id"], "sku_name": name[b["sku_id"]],
            "quantity": stock, "days_to_expiry": days, "naive_daily_demand": round(demand, 1),
            "hold_unsold": round(unsold_hold), "at_risk": is_risk,
            "baseline_units_sold": round(base_units), "baseline_net_recovery_inr": round(base_rev, 2),
        })

    path = OUT / "baseline_results.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0].keys()))
        w.writeheader()
        w.writerows(out_rows)

    print(f"ELASTICITY = {ELASTICITY} (assumption)")
    print(f"batches simulated: {len(out_rows)}, at risk of expiring unsold: {at_risk}")
    print(f"at-risk batches: hold revenue = Rs {tot_hold:,.0f}; fixed-rule baseline revenue = Rs {tot_base:,.0f}")
    print(f"at-risk batches where the fixed rule earns LESS than doing nothing: {worse} of {at_risk}")
    for r in out_rows:
        if r["batch_id"] in ("B-1042", "B-1043"):
            print(r)
    print(f"wrote {path.name}")


if __name__ == "__main__":
    main()
