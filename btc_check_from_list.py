import requests

INPUT_FILE = "c:/Users/vubat/Desktop/New Text Document.txt"
OUTPUT_FILE = "btc_balances_from_list.txt"
BLOCKSTREAM_API = "https://blockstream.info/api/address/{}"

def get_btc_balance(address: str) -> int:
    url = BLOCKSTREAM_API.format(address)
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            return data.get("chain_stats", {}).get("funded_txo_sum", 0) - data.get("chain_stats", {}).get("spent_txo_sum", 0)
        else:
            return -1
    except Exception:
        return -1

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        addresses = [line.strip() for line in f if line.strip()]

    results = []
    for address in addresses:
        balance = get_btc_balance(address)
        results.append(f"{address},{balance}")
        print(f"{address}: {balance}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("address,balance\n")
        for line in results:
            f.write(line + "\n")

if __name__ == "__main__":
    main()
