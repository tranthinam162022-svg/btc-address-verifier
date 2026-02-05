"""
Tạo địa chỉ ví Bitcoin từ danh sách mnemonic trong bip39_1000_private_keys.txt
Ghi ra file btc_addresses_from_mnemonics.txt
"""
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

INPUT_FILE = "bip39_1000_private_keys.txt"
OUTPUT_FILE = "btc_addresses_from_mnemonics.txt"

with open(INPUT_FILE, "r", encoding="utf-8") as f:
    mnemonics = [line.strip() for line in f if line.strip()]

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for idx, mnemonic in enumerate(mnemonics):
        try:
            seed_bytes = Bip39SeedGenerator(mnemonic).Generate()
            btc_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
            btc_node = btc_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
            btc_addr = btc_node.PublicKey().ToAddress()
            out.write(f"{btc_addr}\n")
        except Exception as e:
            out.write(f"ERROR at line {idx+1}: {str(e)}\n")
print(f"Hoàn tất! Đã ghi địa chỉ ví BTC ra {OUTPUT_FILE}")
