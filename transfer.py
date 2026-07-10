from web3 import Web3
from eth_account import Account
from utils import list_wallets, choose_network, ask_password, decrypt_private_key, NATIVE_SYMBOLS

def choose_wallet(wallets):
    print("=== Wallets ===")
    for w in wallets:
        print(f"[{w['index']}] {w['address']}")
    idx = input("Enter wallet ID: ").strip()
    for w in wallets:
        if str(w["index"]) == idx:
            return w
    raise ValueError("Invalid ID.")

def transfer():
    try:
        network_code, rpc_url = choose_network()
    except ValueError as e:
        print(f"❌ {e}")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        print(f"❌ Check {network_code} RPC connection.")
        return

    symbol = NATIVE_SYMBOLS.get(network_code, network_code)

    wallets = list_wallets()
    if not wallets:
        print("No wallet found.")
        return

    sender = choose_wallet(wallets)
    to_address = input("Recipient: ").strip()
    amount_native = input(f"{symbol} value: ").strip()

    if not w3.is_address(to_address):
        print("❌ Invalid recipient.")
        return

    try:
        amount_wei = w3.to_wei(float(amount_native), "ether")
    except ValueError:
        print("❌ Invalid value.")
        return

    password = ask_password()
    try:
        private_key = decrypt_private_key(sender["keystore"], password)
    except ValueError as e:
        print(f"❌ {e}")
        return

    from_address = Web3.to_checksum_address(sender["address"])
    to_address = Web3.to_checksum_address(to_address)

    nonce = w3.eth.get_transaction_count(from_address)
    chain_id = w3.eth.chain_id
    latest_block = w3.eth.get_block("latest")

    if "baseFeePerGas" in latest_block:
        try:
            priority_fee = w3.eth.max_priority_fee
        except Exception:
            priority_fee = w3.to_wei(1, "gwei")
        base_fee = latest_block["baseFeePerGas"]
        max_fee = base_fee * 2 + priority_fee
        tx = {
            "chainId": chain_id,
            "nonce": nonce,
            "to": to_address,
            "value": amount_wei,
            "gas": 21000,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee,
        }
    else:
        gas_price = w3.eth.gas_price
        tx = {
            "chainId": chain_id,
            "nonce": nonce,
            "to": to_address,
            "value": amount_wei,
            "gas": 21000,
            "gasPrice": gas_price,
        }

    print("\n📄 Transaction:")
    print(f"  Chain : {network_code}")
    print(f"  From  : {from_address}")
    print(f"  To    : {to_address}")
    print(f"  Value : {amount_native} {symbol}")
    confirm = input("Confirm (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Canceled.")
        private_key = None
        return

    signed_tx = Account.sign_transaction(tx, private_key)
    private_key = None
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    print(f"\n✅ Transaction sent. TX Hash:\n{tx_hash.hex()}")

if __name__ == "__main__":
    transfer()