"""
FreshSense AI — Algorand API
Deploy on Render. Set SENDER_MNEMONIC as an environment variable.
"""

import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal

from algorand_freshness import store_freshness_on_chain, verify_freshness_from_chain
import algorand_freshness as af

# Override mnemonic from environment variable (set this on Render)
af.SENDER_MNEMONIC = os.environ.get("SENDER_MNEMONIC", af.SENDER_MNEMONIC)

app = FastAPI(title="FreshSense AI — Algorand API")


class FreshnessRequest(BaseModel):
    batch_id:        str
    fruit_type:      str
    freshness_level: Literal["Fresh", "Medium", "Spoiled"]
    co2_ppm:         float = Field(..., gt=0)
    ethanol_ppm:     float = Field(..., ge=0)
    ammonia_ppm:     float = Field(..., ge=0)
    temperature_c:   float
    humidity_pct:    float = Field(..., ge=0, le=100)


@app.post("/store")
def store(req: FreshnessRequest):
    """Store fruit freshness data on Algorand. Returns TX ID + Explorer URL."""
    try:
        tx_id = store_freshness_on_chain(
            req.batch_id, req.fruit_type, req.freshness_level,
            req.co2_ppm, req.ethanol_ppm, req.ammonia_ppm,
            req.temperature_c, req.humidity_pct,
        )
        return {
            "tx_id":        tx_id,
            "explorer_url": f"https://testnet.explorer.perawallet.app/tx/{tx_id}",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/verify/{tx_id}")
def verify(tx_id: str):
    """Fetch and decode a previously stored freshness transaction."""
    try:
        return verify_freshness_from_chain(tx_id)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok"}
