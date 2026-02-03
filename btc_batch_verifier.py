"""Batch BTC address verifier — improved and testable.

Features:
- CLI with --input, --secret-type/auto, --no-api, --rate-delay, --retries, --timeout
- Safe parsing and detection of secret type
- Robust hdwallet calls with error handling
- Optional API calls with retries/backoff
- Logging instead of bare prints
"""
import argparse
import json
import logging
import re
import sys
import time
from time import sleep
from typing import Tuple, Optional

from hdwallet import HDWallet
from hdwallet.symbols import BTC
from btc_com import explorer as btc_explorer


logger = logging.getLogger(__name__)


def detect_secret_type(secret: str) -> str:
    """Heuristics to detect secret type."""
    s = secret.strip()
    if not s:
        return "unknown"
    if " " in s:
        return "mnemonic"
    if s.startswith(("xprv", "xpub", "tprv", "tpub")):
        return "extended"
    if s[0] in ("5", "K", "L") and 50 >= len(s) >= 51:
        # WIF typical lengths 51 (compressed/uncompressed variants)
        return "WIF"
    if len(s) == 64 and re.fullmatch(r"[0-9a-fA-F]{64}", s):
        return "classic"
    if s.startswith("S"):
        # mini private keys sometimes start with S
        return "mini"
    return "unknown"


def btc_address_from_private_key(my_secret: str, secret_type: str = "auto") -> str:
    """Return p2pkh address or empty string on failure."""
    if secret_type == "auto":
        secret_type = detect_secret_type(my_secret)
    if secret_type not in ["WIF", "classic", "extended", "mnemonic", "mini"]:
        raise ValueError(f"Unsupported secret_type: {secret_type}")

    hdwallet = HDWallet(symbol=BTC)

    try:
        if secret_type == "WIF":
            hdwallet.from_wif(wif=my_secret)
        elif secret_type == "classic":
            hdwallet.from_private_key(private_key=my_secret)
        elif secret_type == "extended":
            hdwallet.from_xprivate_key(xprivate_key=my_secret)
        elif secret_type == "mnemonic":
            raise NotImplementedError("Mnemonic secrets not implemented")
        elif secret_type == "mini":
            raise NotImplementedError("Mini private key not implemented")
    except Exception as exc:
        logger.warning("Failed deriving address from secret (type=%s): %s", secret_type, exc)
        return ""

    # Optionally dump for debugging: logger.debug(json.dumps(hdwallet.dumps(), indent=2))
    try:
        return hdwallet.p2pkh_address()
    except Exception as exc:
        logger.exception("Failed to get p2pkh address: %s", exc)
        return ""


def fetch_balance_for_btc_address(btc_address: str, retries: int = 3, timeout: int = 10, rate_delay: float = 1.0) -> Optional[Tuple[int, int]]:
    """Fetch balance and tx_count with simple retry/backoff. Returns (balance, tx_count) or None on failure."""
    backoff = 1.0
    for attempt in range(1, retries + 1):
        try:
            addr_info = btc_explorer.get_address(btc_address)
            # Be polite with API
            sleep(rate_delay)
            return addr_info.balance, addr_info.tx_count
        except Exception as exc:
            logger.warning("Attempt %d: failed to fetch address info for %s: %s", attempt, btc_address, exc)
            if attempt < retries:
                sleep(backoff)
                backoff *= 2
                continue
            logger.error("All attempts failed for %s", btc_address)
            return None


def parse_args(argv):
    parser = argparse.ArgumentParser(description="Batch BTC address verifier")
    parser.add_argument("--input", "-i", default="my_potential_btc_keys.txt", help="Input file with one secret per line")
    parser.add_argument("--secret-type", "-t", default="auto", choices=["auto", "WIF", "classic", "extended", "mnemonic", "mini"], help="Secret type or auto-detect")
    parser.add_argument("--no-api", action="store_true", help="Don't call blockchain APIs (fast, for testing)")
    parser.add_argument("--rate-delay", type=float, default=1.0, help="Delay in seconds between API calls")
    parser.add_argument("--retries", type=int, default=3, help="API retries on failure")
    parser.add_argument("--timeout", type=int, default=10, help="API timeout in seconds (not all libs support it)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable debug logging")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv or sys.argv[1:])
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    try:
        with open(args.input, "r", encoding="utf-8") as fp:
            for line_number, line in enumerate(fp, start=1):
                my_secret = line.strip()
                if not my_secret or my_secret.startswith("#"):
                    continue

                secret_type = args.secret_type if args.secret_type != "auto" else detect_secret_type(my_secret)
                address = ""
                try:
                    address = btc_address_from_private_key(my_secret, secret_type=secret_type)
                except NotImplementedError as exc:
                    logger.warning("Line %d: unsupported secret type for secret=%s: %s", line_number, my_secret, exc)
                    continue
                except ValueError as exc:
                    logger.warning("Line %d: invalid secret type detection: %s", line_number, exc)
                    continue

                if not address:
                    logger.info("Line %d: secret could not be converted to address: %s", line_number, my_secret)
                    continue

                if args.no_api:
                    logger.info("secret: %s address: %s", my_secret, address)
                else:
                    bal = fetch_balance_for_btc_address(address, retries=args.retries, timeout=args.timeout, rate_delay=args.rate_delay)
                    if bal is None:
                        logger.info("secret: %s address: %s balance: <error>", my_secret, address)
                    else:
                        balance, tx_count = bal
                        logger.info("secret: %s address: %s tx_count: %s balance: %s", my_secret, address, tx_count, balance)

    except FileNotFoundError:
        logger.error("Input file not found: %s", args.input)


if __name__ == "__main__":
    main()


