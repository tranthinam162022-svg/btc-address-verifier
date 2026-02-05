"""Check BTC balances using Blockchain.com API (more reliable than Blockstream).

This uses blockchain.com's public API which has better rate limits.
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import OrderedDict
from typing import List

import requests

DEFAULT_INPUT = "51k số.txt"
DEFAULT_ADDR_OUT = "addresses_only.txt"
DEFAULT_BAL_OUT = "btc_balances_blockchain.csv"


def extract_addresses(input_path: str) -> List[str]:
    """Extract unique addresses from CSV file."""
    addresses: "OrderedDict[str, None]" = OrderedDict()
    with open(input_path, "r", encoding="utf-8", newline="") as f:
        sample = f.read(4096)
        f.seek(0)
        has_header = sample.lower().startswith("hex_private_key")
        if has_header:
            reader = csv.DictReader(f)
            for row in reader:
                addr = (row.get("bitcoin_address") or "").strip()
                if addr:
                    addresses.setdefault(addr, None)
        else:
            reader = csv.reader(f)
            for row in reader:
                if not row:
                    continue
                addr = ""
                if len(row) >= 3:
                    addr = row[2].strip()
                elif len(row) == 1:
                    addr = row[0].strip()
                if addr:
                    addresses.setdefault(addr, None)
    return list(addresses.keys())


def fetch_balance_blockchain(address: str, timeout: int = 20) -> tuple[int, int]:
    """Fetch balance from blockchain.com API.
    
    Returns (final_balance_sats, total_received_sats)
    """
    url = f"https://blockchain.info/rawaddr/{address}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        final_balance = int(data.get("final_balance", 0))
        total_received = int(data.get("total_received", 0))
        return final_balance, total_received
    except Exception as exc:
        print(json.dumps({"error": str(exc), "address": address}))
        return -1, -1


def check_balances(
    addresses: List[str],
    output_path: str,
    delay: float = 0.3,
    limit: int | None = None,
) -> None:
    """Check balances sequentially with delay."""
    addr_list = addresses[:limit] if limit else addresses
    
    print(f"Checking {len(addr_list)} addresses...")
    results = []
    
    for idx, addr in enumerate(addr_list, start=1):
        final_balance, total_received = fetch_balance_blockchain(addr)
        total_btc = final_balance / 100_000_000
        results.append((addr, final_balance, total_received, total_btc))
        
        if idx % 50 == 0:
            print(json.dumps({"checked": idx, "total": len(addr_list)}))
        
        time.sleep(delay)
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["address", "balance_sats", "total_received_sats", "balance_btc"])
        for addr, balance, received, btc in results:
            writer.writerow([addr, balance, received, f"{btc:.8f}"])
    
    print(f"✓ Done! Results saved to {output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check BTC balances using Blockchain.com API")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input CSV file")
    parser.add_argument("--addresses-out", default=DEFAULT_ADDR_OUT, help="Output file for addresses")
    parser.add_argument("--balances-out", default=DEFAULT_BAL_OUT, help="Output CSV with balances")
    parser.add_argument("--delay", type=float, default=0.3, help="Delay between requests (seconds)")
    parser.add_argument("--limit", type=int, help="Limit number of addresses to check")
    args = parser.parse_args()

    addresses = extract_addresses(args.input)
    if not addresses:
        print("No addresses found.")
        return

    print(f"Extracted {len(addresses)} unique addresses")
    
    check_balances(addresses, args.balances_out, delay=args.delay, limit=args.limit)


if __name__ == "__main__":
    main()
