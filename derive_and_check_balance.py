"""Extract BTC addresses from a CSV and check balances via Blockstream API.

Default input format (CSV): hex_private_key,wif_private_key,bitcoin_address
Outputs:
  - addresses_only.txt (one address per line)
  - btc_balances.csv (address,confirmed_sats,mempool_sats,total_sats,total_btc)
"""
from __future__ import annotations

import argparse
import csv
import json
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Iterable, List, Tuple

import requests

DEFAULT_INPUT = "51k số.txt"
DEFAULT_ADDR_OUT = "addresses_only.txt"
DEFAULT_BAL_OUT = "btc_balances.csv"
API_BASE = "https://blockstream.info/api"


def extract_addresses(input_path: str) -> List[str]:
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


def write_addresses(addresses: Iterable[str], output_path: str) -> None:
	with open(output_path, "w", encoding="utf-8", newline="") as f:
		for addr in addresses:
			f.write(f"{addr}\n")


def fetch_balance(session: requests.Session, address: str, retries: int = 7, timeout: int = 40) -> Tuple[int, int, int]:
    url = f"{API_BASE}/address/{address}"
    last_err: Exception | None = None
    for attempt in range(retries):
        try:
            resp = session.get(url, timeout=timeout)
            if resp.status_code == 429:
                sleep_time = min(10 * (2 ** attempt), 120)  # Exponential backoff up to 120s
                time.sleep(sleep_time)
                continue
            resp.raise_for_status()
            data = resp.json()
            chain = data.get("chain_stats", {})
            mempool = data.get("mempool_stats", {})
            confirmed = int(chain.get("funded_txo_sum", 0)) - int(chain.get("spent_txo_sum", 0))
            mempool_delta = int(mempool.get("funded_txo_sum", 0)) - int(mempool.get("spent_txo_sum", 0))
            total = confirmed + mempool_delta
            return confirmed, mempool_delta, total
        except Exception as exc:  # noqa: BLE001
            last_err = exc
            sleep_time = min(3 * (attempt + 1), 20)
            time.sleep(sleep_time)
    raise RuntimeError(f"Failed to fetch {address}") from last_err


def check_balances(
    addresses: Iterable[str],
    output_path: str,
    workers: int = 1,
    limit: int | None = None,
    delay: float = 0.5,
) -> None:
    addr_list = list(addresses)
    if limit:
        addr_list = addr_list[:limit]
    
    print(f"Checking {len(addr_list)} addresses with {workers} workers...")
    results = []
    
    if workers == 1:
        # Sequential processing with delay
        with requests.Session() as session:
            for idx, addr in enumerate(addr_list, start=1):
                try:
                    confirmed, mempool_delta, total = fetch_balance(session, addr)
                    total_btc = total / 100_000_000
                    results.append((addr, confirmed, mempool_delta, total, total_btc))
                    if idx % 50 == 0:
                        print(json.dumps({"checked": idx, "total": len(addr_list), "last": addr}))
                except Exception as exc:
                    print(json.dumps({"error": str(exc), "address": addr, "checked": idx}))
                    results.append((addr, -1, -1, -1, -1))
                time.sleep(delay)
    else:
        # Parallel processing
        completed = 0
        with requests.Session() as session:
            with ThreadPoolExecutor(max_workers=workers) as executor:
                futures = {executor.submit(fetch_balance, session, addr): addr for addr in addr_list}
                for future in as_completed(futures):
                    addr = futures[future]
                    completed += 1
                    try:
                        confirmed, mempool_delta, total = future.result()
                        total_btc = total / 100_000_000
                        results.append((addr, confirmed, mempool_delta, total, total_btc))
                        if completed % 50 == 0:
                            print(json.dumps({"checked": completed, "total": len(addr_list), "last": addr}))
                    except Exception as exc:
                        print(json.dumps({"error": str(exc), "address": addr, "checked": completed}))
                        results.append((addr, -1, -1, -1, -1))
    
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["address", "confirmed_sats", "mempool_sats", "total_sats", "total_btc"])
        for addr, confirmed, mempool_delta, total, total_btc in results:
            writer.writerow([addr, confirmed, mempool_delta, total, f"{total_btc:.8f}"])


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract BTC addresses and check balances")
    parser.add_argument("--input", default=DEFAULT_INPUT, help="Input CSV file")
    parser.add_argument("--addresses-out", default=DEFAULT_ADDR_OUT, help="Output file for addresses")
    parser.add_argument("--balances-out", default=DEFAULT_BAL_OUT, help="Output CSV with balances")
    parser.add_argument("--workers", type=int, default=1, help="Number of parallel workers (1 for sequential)")
    parser.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds (for sequential mode)")
    parser.add_argument("--limit", type=int, help="Optional limit for number of addresses")
    args = parser.parse_args()

    addresses = extract_addresses(args.input)
    if not addresses:
        print("No addresses found.")
        return

    write_addresses(addresses, args.addresses_out)
    print(f"Extracted {len(addresses)} addresses to {args.addresses_out}")

    check_balances(addresses, args.balances_out, workers=args.workers, limit=args.limit, delay=args.delay)
    print(f"Balances saved to {args.balances_out}")


if __name__ == "__main__":
	main()
