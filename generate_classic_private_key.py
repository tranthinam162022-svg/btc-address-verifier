import os
import hashlib
import base58

def generate_private_key_hex():
    return os.urandom(32).hex()

def private_key_to_wif(hex_key):
    prefix = b'\x80'  # Mainnet
    key_bytes = bytes.fromhex(hex_key)
    extended = prefix + key_bytes
    checksum = hashlib.sha256(hashlib.sha256(extended).digest()).digest()[:4]
    wif = base58.b58encode(extended + checksum)
    return wif.decode()

if __name__ == "__main__":
    hex_key = generate_private_key_hex()
    wif_key = private_key_to_wif(hex_key)
    print("Private key (hex):", hex_key)
    print("Private key (WIF):", wif_key)
