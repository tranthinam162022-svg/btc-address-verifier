"""
Sinh 500000 mnemonic hợp lệ, xuất private key và địa chỉ cho cả BTC và ETH.
Cảnh báo: File xuất ra sẽ rất lớn, hãy đảm bảo đủ dung lượng ổ đĩa!
"""
import secrets
from bip_utils import Bip39MnemonicGenerator, Bip39WordsNum, Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes

OUTPUT_FILE = "btc_eth_500000.txt"

with open(OUTPUT_FILE, "w", encoding="utf-8") as out:
    for i in range(500000):
        mnemonic = Bip39MnemonicGenerator().FromWordsNumber(Bip39WordsNum.WORDS_NUM_12)
        seed_bytes = Bip39SeedGenerator(str(mnemonic)).Generate()
        # BTC
        btc_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.BITCOIN)
        btc_node = btc_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        btc_priv = btc_node.PrivateKey().Raw().ToHex()
        btc_addr = btc_node.PublicKey().ToAddress()
        # ETH
        eth_ctx = Bip44.FromSeed(seed_bytes, Bip44Coins.ETHEREUM)
        eth_node = eth_ctx.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(0)
        eth_priv = eth_node.PrivateKey().Raw().ToHex()
        eth_addr = eth_node.PublicKey().ToAddress()
        out.write(f"{mnemonic}\nBTC: {btc_addr} | {btc_priv}\nETH: {eth_addr} | {eth_priv}\n---\n")
        if (i+1) % 1000 == 0:
            print(f"Đã sinh {i+1}/500000 mnemonic...")
print(f"Hoàn tất! Đã ghi ra {OUTPUT_FILE}")
