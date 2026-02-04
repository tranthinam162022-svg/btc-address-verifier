"""Derive BTC addresses (P2PKH, P2SH-P2WPKH, P2WPKH) from a BIP39 mnemonic.

Usage: python derive_addresses.py
- Securely enter mnemonic (hidden input) or pass --mnemonic-file <path>.
- Prints derived address info for BIP44 (legacy), BIP49 (P2SH-P2WPKH), BIP84 (Bech32/P2WPKH).

Security: Do not paste your mnemonic in public chats. Use a local env or file.
"""
import argparse
import json
import sys
import getpass
from typing import Dict

from bip_utils import (
    Bip39SeedGenerator,
    Bip44, Bip44Coins,
    Bip49, Bip49Coins,
    Bip84, Bip84Coins,
    Bip44Changes,
)


def load_mnemonic(args) -> str:
    if args.mnemonic_file:
        with open(args.mnemonic_file, "r", encoding="utf-8") as f:
            return f.read().strip()
    if args.mnemonic:
        # Warning: passing mnemonic on CLI may expose it in process lists / history
        print("WARNING: Passing mnemonic on CLI may be insecure.")
        return args.mnemonic.strip()
    # Secure interactive input
    return getpass.getpass("Enter mnemonic (hidden): ").strip()


def derive_for_ctx(ctx, index: int, account: int = 0, change: int = 0) -> Dict:
    node = ctx.Purpose().Coin().Account(account).Change(Bip44Changes.CHAIN_EXT if change == 0 else Bip44Changes.CHAIN_INT).AddressIndex(index)
    priv_obj = node.PrivateKey()
    pub_obj = node.PublicKey()
    return {
        "path": node.Path().ToString(),
        "address": pub_obj.ToAddress(),
        "private_hex": priv_obj.Raw().ToHex(),
        "wif": priv_obj.ToWif(),
        "pub_hex": pub_obj.RawCompressed().ToHex(),
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="Derive BTC addresses from mnemonic (BIP44/BIP49/BIP84)")
    parser.add_argument("--mnemonic-file", help="Path to file containing mnemonic (one line)")
    parser.add_argument("--mnemonic", help="Mnemonic string (insecure to use on shared systems)")
    parser.add_argument("--index", type=int, default=0, help="Address index to derive (default 0)")
    parser.add_argument("--count", type=int, default=1, help="Number of sequential addresses to derive")
    parser.add_argument("--account", type=int, default=0, help="Account index (default 0)")
    parser.add_argument("--change", type=int, default=0, choices=[0,1], help="Change chain (0 external, 1 internal)")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args(argv)

    mnemonic = load_mnemonic(args)
    if not mnemonic:
        print("No mnemonic provided, aborting.")
        sys.exit(1)

    seed_bytes = Bip39SeedGenerator(mnemonic).Generate()

    bip44_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
    bip49_ctx = Bip49.FromSeed(seed_bytes, Bip49Coins.BITCOIN)
    bip84_ctx = Bip84.FromSeed(seed_bytes, Bip84Coins.BITCOIN)

    results = []
    for i in range(args.index, args.index + args.count):
        item = {
            "index": i,
            "bip44": derive_for_ctx(bip44_ctx, i, account=args.account, change=args.change),
            "bip49": derive_for_ctx(bip49_ctx, i, account=args.account, change=args.change),
            "bip84": derive_for_ctx(bip84_ctx, i, account=args.account, change=args.change),
        }
        results.append(item)

    if args.json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            print("Index:", r["index"])
            for k in ("bip44", "bip49", "bip84"):
                print(f"  {k}:")
                info = r[k]
                print(f"    path: {info['path']}")
                print(f"    address: {info['address']}")
                print(f"    private_hex: {info['private_hex']}")
                print(f"    wif: {info['wif']}")
            print()


if __name__ == '__main__':
    main()
