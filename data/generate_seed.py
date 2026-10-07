"""Generate SYNTHETIC seed data for the Retail Stock Intelligence prototype.

Standard library only. Run from the project root:
    python3 data/generate_seed.py
Writes CSV files to data/out/. All data is synthetic and reproducible (fixed seed).
Includes the planted demo scenario: Store A overstocked on yogurt (expires in 3 days),
Store B almost out of the same yogurt and 2.1 km away.
"""
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 42
TODAY = date(2026, 10, 7)
HISTORY_DAYS = 90
OUT = Path(__file__).resolve().parent / "out"

STORES = [
    ("S-A", "Store A", "Zone 1", "supermarket"),
    ("S-B", "Store B", "Zone 2", "supermarket"),
    ("S-C", "Store C", "Zone 3", "convenience"),
]
STORE_MULT = {"S-A": 1.0, "S-B": 1.6, "S-C": 1.2}

# sku_id, name, category, shelf_life_days, unit_cost_inr, unit_price_inr, base_daily_demand_at_store_A
SKUS = [
    ("SKU-DAIRY-YOG-400", "Yogurt 400g", "dairy", 14, 28.0, 45.0, 9.5),
    ("SKU-DAIRY-MLK-1L", "Milk 1L", "dairy", 5, 48.0, 62.0, 40.0),
    ("SKU-DAIRY-PNR-200", "Paneer 200g", "dairy", 10, 70.0, 95.0, 8.0),
    ("SKU-DAIRY-CHS-200", "Cheese slices 200g", "dairy", 60, 95.0, 140.0, 4.0),
    ("SKU-BAKE-BRD-400", "Bread 400g", "bakery", 5, 26.0, 40.0, 25.0),
    ("SKU-BAKE-CAK-250", "Cake slice pack", "bakery", 4, 35.0, 60.0, 6.0),
    ("SKU-PROD-TOM-1KG", "Tomato 1kg", "produce", 6, 22.0, 38.0, 30.0),
    ("SKU-PROD-BAN-1DZ", "Banana 1 dozen", "produce", 5, 36.0, 60.0, 15.0),
    ("SKU-PROD-SPN-250", "Spinach 250g", "produce", 3, 12.0, 22.0, 12.0),
    ("SKU-EGGS-EGG-12", "Eggs 12", "eggs", 14, 66.0, 90.0, 14.0),
    ("SKU-PACK-JUC-1L", "Fruit juice 1L", "packaged", 90, 60.0, 95.0, 7.0),
    ("SKU-PACK-BSC-200", "Biscuits 200g", "packaged", 120, 18.0, 30.0, 18.0),
]

# Planted demand overrides: (store, sku) -> units per day
DEMAND_OVERRIDE = {("S-A", "SKU-DAIRY-YOG-400"): 9.5,
                   ("S-B", "SKU-DAIRY-YOG-400"): 30.0,
                   ("S-C", "SKU-DAIRY-YOG-400"): 12.0}

# store_from, store_to, km, minutes (symmetric). These are placeholders; replace
# with Maps Distance Matrix values on Day 4.
DISTANCES = [("S-A", "S-B", 2.1, 9), ("S-A", "S-C", 5.4, 18), ("S-B", "S-C", 3.8, 14)]

DOW_FACTOR = {0: 0.95, 1: 0.9, 2: 0.95, 3: 1.0, 4: 1.1, 5: 1.3, 6: 1.3}  # Mon..Sun


def base_demand(store_id, sku):
    key = (store_id, sku[0])
    if key in DEMAND_OVERRIDE:
        return DEMAND_OVERRIDE[key]
    return sku[6] * STORE_MULT[store_id]


def write_csv(name, header, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / name
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"wrote {path.name}: {len(rows)} rows")


def main():
    rnd = random.Random(SEED)

    write_csv("stores.csv", ["store_id", "store_name", "area", "format"], STORES)
    write_csv("skus.csv",
              ["sku_id", "sku_name", "category", "shelf_life_days", "unit_cost_inr", "unit_price_inr"],
              [s[:6] for s in SKUS])

    dist_rows = []
    for a, b, km, mins in DISTANCES:
        dist_rows.append((a, b, km, mins))
        dist_rows.append((b, a, km, mins))
    write_csv("store_distances.csv", ["from_store_id", "to_store_id", "distance_km", "travel_minutes"], dist_rows)

    sales = []
    for i in range(HISTORY_DAYS):
        d = TODAY - timedelta(days=HISTORY_DAYS - i)   # last day = yesterday
        for st in STORES:
            for sku in SKUS:
                mean = base_demand(st[0], sku) * DOW_FACTOR[d.weekday()]
                units = max(0, round(mean * (1 + rnd.gauss(0, 0.12))))
                sales.append((d.isoformat(), st[0], sku[0], units, sku[5], 0))
    write_csv("daily_sales.csv",
              ["sale_date", "store_id", "sku_id", "units_sold", "price_inr", "discount_pct"], sales)

    batches = []
    batch_no = 2001
    for st in STORES:
        for sku in SKUS:
            if (st[0], sku[0]) in DEMAND_OVERRIDE and sku[0] == "SKU-DAIRY-YOG-400" and st[0] in ("S-A", "S-B"):
                continue  # planted below
            demand = base_demand(st[0], sku)
            if sku[3] <= 30:
                days_left = rnd.randint(1, min(sku[3], 8))
                qty = round(demand * days_left * rnd.uniform(0.7, 1.6))
            else:
                days_left = rnd.randint(20, 80)
                qty = round(demand * days_left * 0.3)
            expiry = TODAY + timedelta(days=days_left)
            received = TODAY - timedelta(days=rnd.randint(0, 3))
            batches.append((f"B-{batch_no}", st[0], sku[0], max(qty, 1), received.isoformat(), expiry.isoformat()))
            batch_no += 1
    # Planted demo scenario
    batches.append(("B-1042", "S-A", "SKU-DAIRY-YOG-400", 120, (TODAY - timedelta(days=4)).isoformat(),
                    (TODAY + timedelta(days=3)).isoformat()))
    batches.append(("B-1043", "S-B", "SKU-DAIRY-YOG-400", 6, (TODAY - timedelta(days=2)).isoformat(),
                    (TODAY + timedelta(days=6)).isoformat()))
    write_csv("batches.csv",
              ["batch_id", "store_id", "sku_id", "quantity_on_hand", "received_date", "expiry_date"], batches)
    print("planted: B-1042 (Store A, 120 yogurts, expires in 3 days), B-1043 (Store B, 6 yogurts)")


if __name__ == "__main__":
    main()
