import os
import re
import json
import base64
import getpass
from eth_account import Account

ENV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")

def ask_password(confirm: bool = False) -> str:
    pwd = getpass.getpass("🔑 Enter Password: ")
    if confirm:
        pwd2 = getpass.getpass("🔑 Confirm Password: ")
        if pwd != pwd2:
            raise ValueError("Passwords are not same.")
    if len(pwd) < 8:
        raise ValueError("Password length should be more than 8 characters.")
    return pwd

def encrypt_private_key(private_key: str, password: str) -> str:
    keystore_dict = Account.encrypt(private_key, password)
    keystore_json = json.dumps(keystore_dict)
    encoded = base64.b64encode(keystore_json.encode("utf-8")).decode("utf-8")
    return encoded

def decrypt_private_key(encoded_keystore: str, password: str) -> str:
    keystore_json = base64.b64decode(encoded_keystore.encode("utf-8")).decode("utf-8")
    keystore_dict = json.loads(keystore_json)
    try:
        private_key_bytes = Account.decrypt(keystore_dict, password)
    except ValueError:
        raise ValueError("Password is wrong.")
    return "0x" + private_key_bytes.hex()

def _read_env_lines():
    if not os.path.exists(ENV_PATH):
        return []
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        return f.readlines()

def _write_env_lines(lines):
    with open(ENV_PATH, "w", encoding="utf-8") as f:
        f.writelines(lines)
    try:
        os.chmod(ENV_PATH, 0o600)
    except OSError:
        pass

def list_wallets():
    lines = _read_env_lines()
    wallets = {}
    pattern_addr = re.compile(r"^WALLET_ADDRESS_(\d+)=(.*)$")
    pattern_key = re.compile(r"^WALLET_KEY_(\d+)=(.*)$")
    for line in lines:
        line = line.strip()
        m1 = pattern_addr.match(line)
        m2 = pattern_key.match(line)
        if m1:
            idx = int(m1.group(1))
            wallets.setdefault(idx, {})["address"] = m1.group(2)
        elif m2:
            idx = int(m2.group(1))
            wallets.setdefault(idx, {})["keystore"] = m2.group(2)
    result = []
    for idx in sorted(wallets.keys()):
        w = wallets[idx]
        if "address" in w and "keystore" in w:
            result.append({"index": idx, "address": w["address"], "keystore": w["keystore"]})
    return result

def add_wallet(address: str, encoded_keystore: str):
    wallets = list_wallets()
    next_idx = (max([w["index"] for w in wallets]) + 1) if wallets else 1
    lines = _read_env_lines()
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    lines.append(f"WALLET_ADDRESS_{next_idx}={address}\n")
    lines.append(f"WALLET_KEY_{next_idx}={encoded_keystore}\n")
    _write_env_lines(lines)
    return next_idx

NATIVE_SYMBOLS = {
    "ETH": "ETH",
    "POL": "POL/MATIC",
    "BNB": "BNB",
    "ARB": "ETH",
    "AVAX": "AVAX",
}

def list_networks():
    lines = _read_env_lines()
    networks = {}
    pattern = re.compile(r"^([A-Z0-9]+)_RPC_URL=(.*)$")
    for line in lines:
        line = line.strip()
        m = pattern.match(line)
        if m:
            networks[m.group(1)] = m.group(2)
    return networks

def choose_network():
    networks = list_networks()
    if not networks:
        raise ValueError("No RPC found")
    codes = list(networks.keys())
    print("=== Chains ===")
    for i, code in enumerate(codes, 1):
        symbol = NATIVE_SYMBOLS.get(code, code)
        print(f"[{i}] {code}  ({symbol})")
    choice = input("Enter chain ID: ").strip()
    try:
        idx = int(choice) - 1
        if idx < 0:
            raise ValueError
        code = codes[idx]
    except (ValueError, IndexError):
        raise ValueError("Invalid ID.")
    return code, networks[code]