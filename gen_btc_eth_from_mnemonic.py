"""
Tạo private key và địa chỉ cho cả Bitcoin (BTC) và Ethereum (ETH) từ mnemonic BIP39.
- Đọc mnemonic từ file hoặc nhập tay.
- In ra private key và địa chỉ cho BTC (BIP44) và ETH (BIP44).
"""
import argparse
import getpass
from bip_utils import (
    Bip39SeedGenerator,
    Bip44, Bip44Coins,
    Bip44Changes,
)

def load_mnemonic(args):
    if args.mnemonic_file:
        with open(args.mnemonic_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if args.mnemonic:
        print("WARNING: Passing mnemonic on CLI may be insecure.")
        return args.mnemonic.strip()
    return getpass.getpass("Enter mnemonic (hidden): ").strip()

def main():
    parser = argparse.ArgumentParser(description="Tạo private key và địa chỉ BTC/ETH từ mnemonic")
    parser.add_argument("--mnemonic-file", help="Đường dẫn file chứa mnemonic")
    parser.add_argument("--mnemonic", help="Chuỗi mnemonic (không khuyến khích nhập trực tiếp)")
    parser.add_argument("--index", type=int, default=0, help="Chỉ số địa chỉ (default 0)")
    args = parser.parse_args()

    mnemonic = load_mnemonic(args)
    if not mnemonic:
        print("Không có mnemonic, dừng lại.")
        return

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    # Bitcoin (BIP44)
    btc_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    btc_node = btc_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(args.index)
    btc_priv = btc_node.PrivateKey().Raw().ToHex()
    btc_addr = btc_node.PublicKey().ToAddress()

    # Ethereum (BIP44)
    eth_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
    eth_node = eth_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(args.index)
    eth_priv = eth_node.PrivateKey().Raw().ToHex()
    eth_addr = eth_node.PublicKey().ToAddress()

    print("--- Bitcoin (BTC) ---")
    print(f"Private key: {btc_priv}")
    print(f"Address:    {btc_addr}")
    print("--- Ethereum (ETH) ---")
    print(f"Private key: {eth_priv}")
    print(f"Address:    {eth_addr}")

if __name__ == "__main__":
    main()
