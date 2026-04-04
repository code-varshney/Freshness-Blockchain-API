"""
FreshSense AI — Algorand Blockchain Logger
Stores fruit freshness data in a transaction note field.
Returns a transaction ID as proof of authenticity.
"""

import json
import base64
from datetime import datetime, timezone

from algosdk import account, mnemonic
from algosdk.v2client import algod
from algosdk.transaction import PaymentTxn, wait_for_confirmation

# ── Algorand Testnet node (AlgoNode — no sign-up required) ──────────────────
ALGOD_ADDRESS = "https://testnet-api.algonode.cloud"
ALGOD_TOKEN   = ""                          # AlgoNode requires no token
ALGOD_HEADERS = {"X-API-Key": ALGOD_TOKEN}

# ── Replace with your funded Testnet account ─────────────────────────────────
# Generate one at: https://bank.testnet.algorand.network/
SENDER_MNEMONIC = (
    "yellow hawk dial have galaxy style spread sell initial casual believe control tray reason concert mixture hole gospel shoulder monkey hen control school absent three"
)


def get_algod_client() -> algod.AlgodClient:
    return algod.AlgodClient(ALGOD_TOKEN, ALGOD_ADDRESS, ALGOD_HEADERS)


def build_freshness_payload(
    batch_id: str,
    fruit_type: str,
    freshness_level: str,   # "Fresh" | "Medium" | "Spoiled"
    co2_ppm: float,
    ethanol_ppm: float,
    ammonia_ppm: float,
    temperature_c: float,
    humidity_pct: float,
) -> dict:
    """Returns a compact dict that fits inside a 1 KB transaction note."""
    return {
        "app":       "FreshSenseAI",
        "batch":     batch_id,
        "fruit":     fruit_type,
        "level":     freshness_level,
        "co2":       co2_ppm,
        "ethanol":   ethanol_ppm,
        "ammonia":   ammonia_ppm,
        "temp_c":    temperature_c,
        "humidity":  humidity_pct,
        "ts":        datetime.now(timezone.utc).isoformat(),
    }


def store_freshness_on_chain(
    batch_id: str,
    fruit_type: str,
    freshness_level: str,
    co2_ppm: float,
    ethanol_ppm: float,
    ammonia_ppm: float,
    temperature_c: float,
    humidity_pct: float,
) -> str:
    """
    Sends a 0-ALGO self-transaction carrying the freshness payload in the
    note field.  Returns the transaction ID (use it on Algorand Explorer).
    """
    client       = get_algod_client()
    private_key  = mnemonic.to_private_key(SENDER_MNEMONIC)
    sender       = account.address_from_private_key(private_key)
    params       = client.suggested_params()

    payload      = build_freshness_payload(
        batch_id, fruit_type, freshness_level,
        co2_ppm, ethanol_ppm, ammonia_ppm,
        temperature_c, humidity_pct,
    )
    note_bytes   = json.dumps(payload, separators=(",", ":")).encode()

    # 0-ALGO self-transaction — cheapest way to anchor data on-chain
    txn          = PaymentTxn(
        sender   = sender,
        sp       = params,
        receiver = sender,
        amt      = 0,
        note     = note_bytes,
    )
    signed_txn   = txn.sign(private_key)
    tx_id        = client.send_transaction(signed_txn)
    wait_for_confirmation(client, tx_id, wait_rounds=4)

    explorer_url = f"https://testnet.explorer.perawallet.app/tx/{tx_id}"
    print(f"✅ Stored on-chain!\n   TX ID : {tx_id}\n   View  : {explorer_url}")
    return tx_id


def verify_freshness_from_chain(tx_id: str) -> dict:
    """
    Fetches a previously stored transaction and decodes the freshness payload.
    Useful for the mobile app's 'Verify Batch' screen.
    """
    client  = get_algod_client()
    tx_info = client.pending_transaction_info(tx_id)
    note    = tx_info.get("note") or tx_info.get("txn", {}).get("txn", {}).get("note", "")
    raw_note = base64.b64decode(note).decode()
    return json.loads(raw_note)


# ── Quick demo ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    tx_id = store_freshness_on_chain(
        batch_id        = "BATCH-2025-001",
        fruit_type      = "Mango",
        freshness_level = "Fresh",
        co2_ppm         = 412.5,
        ethanol_ppm     = 0.8,
        ammonia_ppm     = 0.3,
        temperature_c   = 22.4,
        humidity_pct    = 65.2,
    )

    print("\n🔍 Verifying stored data...")
    data = verify_freshness_from_chain(tx_id)
    print(json.dumps(data, indent=2))
