import json
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).resolve().parent
CONTRACTS = BASE.parent / "contracts"
STATIC = BASE / "static"
ALLOWED = {"at_risk_batch", "option_results", "decision_output"}

app = FastAPI(title="Retail Stock Intelligence (prototype)")


def load(name: str) -> dict:
    if name not in ALLOWED:
        raise HTTPException(status_code=404, detail="Unknown contract")
    return json.loads((CONTRACTS / f"{name}.json").read_text(encoding="utf-8"))


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/contracts/{name}")
def contract(name: str):
    return load(name)


@app.get("/api/demo")
def demo():
    """Combined example payload so the frontend can be built before real data exists."""
    return {name: load(name) for name in sorted(ALLOWED)}


# Static dashboard must be mounted last so it does not shadow the API routes.
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
