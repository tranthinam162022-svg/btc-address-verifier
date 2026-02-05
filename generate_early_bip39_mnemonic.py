import os
import random

def load_bip39_wordlist(path="bip39-words.txt"):
    with open(path, "r", encoding="utf-8") as f:
        return [w.strip() for w in f if w.strip()]

def generate_mnemonic_2013(wordlist, num_words=12):
    # BIP39 (2013) phổ biến nhất là 12 từ
    return " ".join(random.choice(wordlist) for _ in range(num_words))

if __name__ == "__main__":
    wordlist = load_bip39_wordlist()
    mnemonic = generate_mnemonic_2013(wordlist)
    print("Mnemonic (2013):", mnemonic)
