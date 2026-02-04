import subprocess
import os

MNEMONIC_FILE = "bip39_1000_private_keys.txt"
OUTPUT_FILE = "derived_addresses.txt"
SCRIPT = "derive_addresses.py"

with open(MNEMONIC_FILE, "r", encoding="utf-8") as f:
    mnemonics = [line.strip() for line in f if line.strip()]

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for idx, mnemonic in enumerate(mnemonics):
        print(f"Đang xử lý mnemonic thứ {idx+1}...")
        result = subprocess.run([
            "python", SCRIPT,
            "--mnemonic", mnemonic,
            "--json"
        ], capture_output=True, text=True)
        out.write(result.stdout)
        out.write("\n")
        print(f"Đã ghi kết quả cho mnemonic thứ {idx+1}")

print(f"Hoàn tất! Địa chỉ ví đã được ghi vào {OUTPUT_FILE}")
