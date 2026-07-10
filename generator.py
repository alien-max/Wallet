from eth_account import Account
from utils import ask_password, encrypt_private_key, add_wallet

def generate_wallet():
    print("=== Generating new wallet ===")
    password = ask_password(confirm=True)

    acct = Account.create()
    private_key = acct.key.hex()
    address = acct.address

    print("\n⏳ Encrypting PK...")
    encoded_keystore = encrypt_private_key(private_key, password)
    idx = add_wallet(address, encoded_keystore)

    print("\n✅ Wallet saved.")
    print(f"ID : {idx}")
    print(f"Address : {address}")

if __name__ == "__main__":
    generate_wallet()