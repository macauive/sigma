"""
Weekly script: refresh profitable_tokens.json from Dune Analytics.

Run manually or via cron:
  cd /Users/iver/Projects/sigma && python update_profitable_tokens.py

Requires DUNE_API_KEY in private.env (https://dune.com/settings/api).
Falls back to extending the existing list on API failure.
"""
import json
import os
import time
import requests
from datetime import date
from dotenv import load_dotenv

load_dotenv("private.env")

DUNE_API_KEY = os.getenv("DUNE_API_KEY", "")
OUTPUT_FILE = "profitable_tokens.json"
MAX_TOKENS = 500

# Dune query IDs (create these queries in the Dune UI and paste the IDs here)
# Query logic: SELECT token_out, SUM(profit_usd) as total_profit
#              FROM sandwich_attacks WHERE block_time > NOW() - INTERVAL '30 days'
#              GROUP BY 1 ORDER BY 2 DESC LIMIT 500
DUNE_QUERY_ID = os.getenv("DUNE_SANDWICH_QUERY_ID", "")  # e.g. "3456789"


def run_dune_query(query_id: str, api_key: str) -> list[str]:
    """Execute a Dune query and return a list of token addresses."""
    headers = {"X-Dune-API-Key": api_key}

    # Trigger query execution
    r = requests.post(
        f"https://api.dune.com/api/v1/query/{query_id}/execute",
        headers=headers,
        json={"performance": "medium"},
        timeout=10,
    )
    if r.status_code != 200:
        raise RuntimeError(f"Dune execute failed {r.status_code}: {r.text[:200]}")

    execution_id = r.json()["execution_id"]
    print(f"[dune] Execution started: {execution_id}")

    # Poll until done (max 120s)
    for _ in range(24):
        time.sleep(5)
        r2 = requests.get(
            f"https://api.dune.com/api/v1/execution/{execution_id}/status",
            headers=headers, timeout=10,
        )
        state = r2.json().get("state", "")
        print(f"[dune] State: {state}")
        if state == "QUERY_STATE_COMPLETED":
            break
        if state in ("QUERY_STATE_FAILED", "QUERY_STATE_CANCELLED"):
            raise RuntimeError(f"Dune query {state}")
    else:
        raise RuntimeError("Dune query timed out after 120s")

    # Fetch results
    r3 = requests.get(
        f"https://api.dune.com/api/v1/execution/{execution_id}/results",
        headers=headers, timeout=10,
    )
    rows = r3.json().get("result", {}).get("rows", [])

    # Extract token addresses from first column
    tokens = []
    for row in rows[:MAX_TOKENS]:
        addr = row.get("token_out") or row.get("token_address") or ""
        if addr and addr.startswith("0x") and len(addr) == 42:
            tokens.append(addr)

    return tokens


def main():
    existing = []
    try:
        with open(OUTPUT_FILE) as f:
            existing = json.load(f).get("tokens", [])
    except Exception:
        pass

    if not DUNE_API_KEY:
        print("[warn] DUNE_API_KEY not set — keeping existing token list")
        return

    if not DUNE_QUERY_ID:
        print("[warn] DUNE_SANDWICH_QUERY_ID not set — keeping existing token list")
        print("  Create a query at dune.com and set DUNE_SANDWICH_QUERY_ID in private.env")
        return

    try:
        tokens = run_dune_query(DUNE_QUERY_ID, DUNE_API_KEY)
        print(f"[dune] Retrieved {len(tokens)} tokens")
    except Exception as e:
        print(f"[dune] Query failed: {e} — keeping existing list")
        return

    # Merge with existing (Dune tokens take priority, existing fill the rest)
    seen = set(t.lower() for t in tokens)
    for t in existing:
        if t.lower() not in seen and len(tokens) < MAX_TOKENS:
            tokens.append(t)
            seen.add(t.lower())

    payload = {
        "_comment": "Updated weekly by update_profitable_tokens.py",
        "_updated": str(date.today()),
        "_source": f"dune-query-{DUNE_QUERY_ID}",
        "tokens": tokens,
    }
    with open(OUTPUT_FILE, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"[ok] Wrote {len(tokens)} tokens to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
