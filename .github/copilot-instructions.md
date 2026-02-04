# Copilot Instructions for btc-address-verifier

## Project Overview
This repository contains Python scripts for verifying and generating Bitcoin (BTC) addresses using private keys. It supports bulk operations and leverages the `hdwallet` library and Blockstream public APIs for address and balance checks.

## Key Components
- **btc_balance_checker.py**: Checks BTC balances for a list of addresses using Blockstream API.
- **btc_batch_verifier.py**: (See file for details) Likely processes multiple keys/addresses in batch.
- **btc_check_from_list.py**: (See file for details) Likely checks addresses from a provided list.
- **derive_addresses.py**: (See file for details) Likely derives addresses from keys or mnemonics.
- **generate_bip39_priv_keys.py**: Generates BIP39 private keys, possibly using `bip39-words.txt`.
- **bip39_1000_private_keys.txt**: Example or generated private keys for testing.
- **bip39-words.txt**: BIP39 word list for mnemonic generation.
- **my_potential_btc_keys.txt**: Output or input file for potential keys.

## Workflow & Usage
- **Input/Output**: Most scripts read from and write to plain text files. Update `INPUT_FILE` and `OUTPUT_FILE` variables as needed.
- **BTC Balance Check**: `btc_balance_checker.py` reads addresses from `New Text Document.txt` and writes balances to `btc_balances.txt`.
- **Dependencies**: Install requirements with `pip install -r requirements.txt`.
- **No formal test suite**: Testing is manual; check script outputs for correctness.

## Patterns & Conventions
- Scripts are standalone; each has its own entry point (`if __name__ == "__main__":`).
- Input files are expected to be line-delimited lists (addresses, keys, or mnemonics).
- Output files are typically CSV or line-delimited text.
- Uses Blockstream public API for live BTC data.
- Error handling: Scripts return `-1` or skip on API/network errors.

## Integration & Extensibility
- To add new address sources or output formats, update the relevant script and adjust file paths.
- To use a different BTC API, modify the API URL and response parsing logic in the scripts.

## Example: Checking BTC Balances
- Place BTC addresses (one per line) in `New Text Document.txt`.
- Run: `python btc_balance_checker.py`
- Output: `btc_balances.txt` with `address,balance` per line.

## References
- See [README.md](../README.md) for a high-level summary.
- See each script for detailed logic and variable usage.

---
**For AI agents:**
- Always check and update file paths for input/output as needed.
- Respect the standalone nature of each script; avoid unnecessary coupling.
- When adding new scripts, follow the pattern of reading from a file, processing, and writing output.
- Use the `hdwallet` library and Blockstream API as shown in existing scripts.
