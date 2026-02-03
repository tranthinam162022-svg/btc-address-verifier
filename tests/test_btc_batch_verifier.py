import pytest

from hdwallet import HDWallet
from hdwallet.symbols import BTC

from btc_batch_verifier import detect_secret_type, btc_address_from_private_key


def test_detect_secret_type_cases():
    hex_priv = "6cd78b0d69eab1a47bfa53a52b9d8c4331e858b5d7a599270a95d9735fdb0b94"
    assert detect_secret_type(hex_priv) == "classic"

    hd = HDWallet(symbol=BTC)
    hd.from_private_key(private_key=hex_priv)
    wif = hd.wif()
    assert detect_secret_type(wif) == "WIF"

    mnemonic = "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    assert detect_secret_type(mnemonic) == "mnemonic"


def test_btc_address_from_private_key_matches_hdwallet():
    hex_priv = "6cd78b0d69eab1a47bfa53a52b9d8c4331e858b5d7a599270a95d9735fdb0b94"

    hd = HDWallet(symbol=BTC)
    hd.from_private_key(private_key=hex_priv)
    expected = hd.p2pkh_address()

    got = btc_address_from_private_key(hex_priv, secret_type="classic")
    assert got == expected

    wif = hd.wif()
    got2 = btc_address_from_private_key(wif, secret_type="WIF")
    assert got2 == expected


def test_bad_secret_returns_empty():
    assert btc_address_from_private_key("not-a-valid-secret", secret_type="classic") == ""
