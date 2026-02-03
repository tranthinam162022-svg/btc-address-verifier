"""Generate BIP39 mnemonics and derive BTC private keys and addresses.

Usage:
    python generate_bip39_priv_keys.py --count 1000 --out generated_bip39_private_keys.txt

Warning: Generated private keys are sensitive. Keep output secure.
"""
import argparse
from time import sleep
from hdwallet import HDWallet
from hdwallet.symbols import BTC
from hdwallet.utils import generate_mnemonic


def generate_and_dump(count: int, out_path: str):
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("mnemonic\tprivate_hex\twif\taddress\n")
        for i in range(count):
            # Generate a 12-word mnemonic (128 bits strength)
            mnemonic = generate_mnemonic(strength=128, language="english")

            hdwallet = HDWallet(symbol=BTC)
            hdwallet.from_mnemonic(mnemonic=mnemonic, language="english")

            try:
                priv_hex = hdwallet.private_key()
            except Exception:
                priv_hex = ""
            try:
                wif = hdwallet.wif()
            except Exception:
                wif = ""
            try:
                address = hdwallet.p2pkh_address()
            except Exception:
                address = ""

            f.write(f"{mnemonic}\t{priv_hex}\t{wif}\t{address}\n")

            # minor sleep to be nice on systems; also gives a chance to interrupt
            sleep(0.005)


def main():
    parser = argparse.ArgumentParser(description="Generate BIP39 mnemonics and BTC keys")
    parser.add_argument("--count", "-n", type=int, default=1000, help="Number of mnemonics to generate")
    parser.add_argument("--out", "-o", default="generated_bip39_private_keys.txt", help="Output file")
    args = parser.parse_args()

    print(f"Generating {args.count} mnemonics -> {args.out}")
    generate_and_dump(args.count, args.out)
    print("Done.")


if __name__ == '__main__':
    main()
