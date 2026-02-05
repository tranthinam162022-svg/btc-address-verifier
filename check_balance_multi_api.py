"""Check BTC balances using multiple APIs with fallback and long delays.

Uses 3 different APIs with rotation to avoid rate limits:
1. Blockcypher.com (3 req/sec free)
2. Blockchain.com 
3. Blockstream.info
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import OrderedDict
from typing import List, Tuple

import requests

DEFAULT_INPUT = "51k số.txt"
DEFAULT_BAL_OUT = "btc_balances_multi.csv"


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


def fetch_blockcypher(address: str, timeout: int = 15) -> Tuple[int, int]:
    """Fetch from blockcypher.com (best rate limits: 3/sec, 200/hr, 2000/day)."""
    url = f"https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        balance = int(data.get("final_balance", 0))
        total_received = int(data.get("total_received", 0))
        return balance, total_received
    except Exception:
        return -1, -1


def fetch_blockchain_com(address: str, timeout: int = 15) -> Tuple[int, int]:
    """Fetch from blockchain.info."""
    url = f"https://blockchain.info/rawaddr/{address}?limit=0"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        final_balance = int(data.get("final_balance", 0))
        total_received = int(data.get("total_received", 0))
        return final_balance, total_received
    except Exception:
        return -1, -1


def fetch_blockstream(address: str, timeout: int = 15) -> Tuple[int, int]:
    """Fetch from blockstream.info."""
    url = f"https://blockstream.info/api/address/{address}"
    try:
        resp = requests.get(url, timeout=timeout)
        resp.raise_for_status()
        data = resp.json()
        funded = int(data.get("chain_stats", {}).get("funded_txo_sum", 0))
        spent = int(data.get("chain_stats", {}).get("spent_txo_sum", 0))
        balance = funded - spent
        return balance, funded
    except Exception:
        return -1, -1


def fetch_with_fallback(address: str, api_order: List[str]) -> Tuple[int, int, str]:
    """Try multiple APIs with fallback.
    
    Returns (balance, total_received, api_used)
    """
    for api_name in api_order:
        if api_name == "blockcypher":
            balance, received = fetch_blockcypher(address)
        elif api_name == "blockchain":
            balance, received = fetch_blockchain_com(address)
        elif api_name == "blockstream":
            balance, received = fetch_blockstream(address)
        else:
            continue
        
        if balance >= 0:  # Success
            return balance, received, api_name
    
    return -1, -1, "all_failed"


def check_balances(
    addresses: List[str],
    output_path: str,
    delay: float = 3.0,
    limit: int | None = None,
) -> None:
    """Check balances with API rotation."""
    addr_list = addresses[:limit] if limit else addresses
    
    print(f"Checking {len(addr_list)} addresses with {delay}s delay...")
    print("Using API rotation: Blockcypher (primary) → Blockchain → Blockstream")
    print(f"Estimated time: {len(addr_list) * delay / 3600:.1f} hours")
    
    results = []
    api_order = ["blockcypher", "blockchain", "blockstream"]
    start_time = time.time()
    
    for idx, addr in enumerate(addr_list, start=1):
        balance, received, api_used = fetch_with_fallback(addr, api_order)
        btc = balance / 100_000_000 if balance >= 0 else 0.0
        results.append((addr, balance, received, btc, api_used))
        
        # Progress updates
        if idx % 10 == 0 or balance > 0:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            remaining_hrs = (len(addr_list) - idx) / rate / 3600 if rate > 0 else 0
            
            print(json.dumps({
                "progress": f"{idx}/{len(addr_list)}",
                "address": addr[:8] + "...",
                "balance_btc": f"{btc:.8f}",
                "api": api_used,
                "remaining_hrs": f"{remaining_hrs:.1f}"
            }))
        
        # Auto-save every 100 addresses
        if idx % 100 == 0:
            _save_results(results, output_path)
            print(f"[AUTO-SAVE] Saved {len(results)} results")
        
        time.sleep(delay)
    
    # Final save
    _save_results(results, output_path)
    
    # Summary
    success = sum(1 for r in results if r[1] >= 0)
    with_balance = sum(1 for r in results if r[1] > 0)
    total_time = (time.time() - start_time) / 3600
    print(f"\n✓ Done! Saved to {output_path}")
    print(f"Success: {success}/{len(addr_list)} | With balance: {with_balance} | Time: {total_time:.1f}h")


def _save_results(results: List[Tuple], output_path: str) -> None:
    """Save results to CSV."""
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["address", "balance_sats", "total_received_sats", "balance_btc", "api_used"])
        for addr, balance, received, btc, api_used in results:
            writer.writerow([addr, balance, received, f"{btc:.8f}", api_used])


def main() -> None:
    parser = argparse.ArgumentParser(description="Check BTC balances with multiple APIs")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input CSV file")
    parser.add_argument("--output", default=DEFAULT_BAL_OUT, help="Output CSV")
    parser.add_argument("--delay", type=float, default=3.0, help="Delay between addresses (seconds)")
    parser.add_argument("--limit", type=int, help="Limit number to check")
    args = parser.parse_args()

    addresses = extract_addresses(args.input)
    if not addresses:
        print("No addresses found.")
        return

    print(f"Extracted {len(addresses)} unique addresses")
    check_balances(addresses, args.output, delay=args.delay, limit=args.limit)


if __name__ == "__main__":
    main()
