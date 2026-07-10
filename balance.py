from web3 import Web3
from utils import list_wallets, choose_network, NATIVE_SYMBOLS

def show_balances():
    try:
        network_code, rpc_url = choose_network()
    except ValueError as e:
        print(f"❌ {e}")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))

    if not w3.is_connected():
        print(f"❌ Check {network_code} RPC connection.")
        return

    wallets = list_wallets()
    if not wallets:
        print("No wallet found.")
        return

    symbol = NATIVE_SYMBOLS.get(network_code, network_code)
    print(f"\n=== Wallets balance on {network_code} ===")
    for w in wallets:
        try:
            balance_wei = w3.eth.get_balance(Web3.to_checksum_address(w["address"]))
            balance_native = w3.from_wei(balance_wei, "ether")
            print(f"[{w['index']}] {w['address']}  ->  {balance_native} {symbol}")
        except Exception as e:
            print(f"[{w['index']}] {w['address']}  ->  Failed: {e}")

if __name__ == "__main__":
    show_balances()