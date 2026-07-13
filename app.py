import streamlit as st
from web3 import Web3
from eth_account import Account
import utils

st.set_page_config(page_title="Wallet Manager - Offline Multi-Chain", page_icon="🔐", layout="centered")
utils.init_db()

if "pending_tx" not in st.session_state:
    st.session_state.pending_tx = None

def get_web3_or_none(network_code: str):
    try:
        code, rpc_url = utils.get_network(network_code)
    except ValueError as e:
        st.error(f"❌ {e}")
        return None, None
    w3 = Web3(Web3.HTTPProvider(rpc_url))
    if not w3.is_connected():
        st.error(f"❌ Check {code} RPC connection.")
        return None, None
    return w3, code

def build_native_transfer_tx(w3: Web3, chain_id: int, from_address: str, to_address: str, amount_wei: int) -> dict:
    nonce = w3.eth.get_transaction_count(from_address)
    latest_block = w3.eth.get_block("latest")

    if "baseFeePerGas" in latest_block:
        try:
            priority_fee = w3.eth.max_priority_fee
        except Exception:
            priority_fee = w3.to_wei(1, "gwei")
        base_fee = latest_block["baseFeePerGas"]
        max_fee = base_fee * 2 + priority_fee
        return {
            "chainId": chain_id,
            "nonce": nonce,
            "to": to_address,
            "value": amount_wei,
            "gas": 21000,
            "maxFeePerGas": max_fee,
            "maxPriorityFeePerGas": priority_fee,
        }

    gas_price = w3.eth.gas_price
    return {
        "chainId": chain_id,
        "nonce": nonce,
        "to": to_address,
        "value": amount_wei,
        "gas": 21000,
        "gasPrice": gas_price,
    }

def page_generate_wallet():
    st.header("🆕 Generate New Wallet")

    wallets = utils.count_wallets()
    placeholder = f"Account {wallets+1}"

    with st.form("generate_wallet_form", clear_on_submit=True):
        name = st.text_input("Wallet name", placeholder=placeholder)
        password = st.text_input("Password", type="password")
        password_confirm = st.text_input("Confirm Password", type="password")
        submitted = st.form_submit_button("Generate Wallet")

    if submitted:
        if password != password_confirm:
            st.error("❌ Passwords are not same.")
            return
        try:
            utils.validate_password(password)
        except ValueError as e:
            st.error(f"❌ {e}")
            return
        
        if not name:
            name = placeholder

        acct = Account.create()
        private_key = acct.key.hex()
        address = acct.address

        with st.spinner("Encrypting private key..."):
            encoded_keystore = utils.encrypt_private_key(private_key, password)
        private_key = None

        idx = utils.add_wallet(address, encoded_keystore, name)
        st.success("✅ Wallet saved.")
        st.write(f"**ID:** {idx}")
        st.write(f"**Name:** {name}")
        st.write(f"**Address:** `{address}`")

def page_wallets_and_balances():
    st.header("💼 Wallets & Balances")

    wallets = utils.list_wallets()
    if not wallets:
        st.info("No wallet found. Generate one first.")
        return

    st.subheader("Saved Wallets")
    st.table([{"ID": w["index"], "Name": w["name"], "Address": w["address"]} for w in wallets])

    networks = utils.list_networks()
    if not networks:
        st.info("No network configured yet. Add one in the 'Networks' page.")
        return

    st.subheader("Check Balances")
    codes = list(networks.keys())
    network_code = st.selectbox("Network", codes, format_func=lambda c: f"{c} ({utils.NATIVE_SYMBOLS.get(c, c)})")

    if st.button("Refresh Balances"):
        w3, code = get_web3_or_none(network_code)
        if not w3:
            return
        symbol = utils.NATIVE_SYMBOLS.get(code, code)

        rows = []
        for w in wallets:
            try:
                balance_wei = w3.eth.get_balance(Web3.to_checksum_address(w["address"]))
                balance_native = w3.from_wei(balance_wei, "ether")
                rows.append({"ID": w["index"], "Name": w["name"], "Address": w["address"], "Balance": f"{balance_native} {symbol}"})
            except Exception as e:
                rows.append({"ID": w["index"], "Name": w["name"], "Address": w["address"], "Balance": f"Failed: {e}"})
        st.table(rows)

def page_transfer():
    st.header("🔁 Transfer")

    wallets = utils.list_wallets()
    networks = utils.list_networks()

    if not wallets:
        st.info("No wallet found. Generate one first.")
        return
    if not networks:
        st.info("No network configured yet. Add one in the 'Networks' page.")
        return

    codes = list(networks.keys())
    network_code = st.selectbox("Network", codes, format_func=lambda c: f"{c} ({utils.NATIVE_SYMBOLS.get(c, c)})", key="tr_network")
    symbol = utils.NATIVE_SYMBOLS.get(network_code, network_code)

    wallet_labels = {f"[{w['name']}] {w['address']}": w for w in wallets}
    sender_label = st.selectbox("Sender wallet", list(wallet_labels.keys()))
    sender = wallet_labels[sender_label]

    to_address = st.text_input("Recipient address")
    amount_native = st.text_input(f"Amount ({symbol})")

    if st.button("Prepare Transaction"):
        w3, code = get_web3_or_none(network_code)
        if not w3:
            return

        if not w3.is_address(to_address):
            st.error("❌ Invalid recipient address.")
            return

        try:
            amount_wei = w3.to_wei(float(amount_native), "ether")
        except ValueError:
            st.error("❌ Invalid amount.")
            return

        st.session_state.pending_tx = {
            "network_code": network_code,
            "wallet_id": sender["index"],
            "from_address": sender["address"],
            "to_address": to_address,
            "amount_native": amount_native,
            "amount_wei": amount_wei,
            "symbol": symbol,
        }

    pending = st.session_state.pending_tx
    if pending:
        st.subheader("📄 Confirm Transaction")
        st.write(f"**Chain:** {pending['network_code']}")
        st.write(f"**From:** `{pending['from_address']}`")
        st.write(f"**To:** `{pending['to_address']}`")
        st.write(f"**Value:** {pending['amount_native']} {pending['symbol']}")

        password = st.text_input("Password to sign", type="password", key="transfer_password")

        col1, col2 = st.columns(2)
        with col1:
            confirm = st.button("✅ Confirm & Send")
        with col2:
            cancel = st.button("❌ Cancel")

        if cancel:
            st.session_state.pending_tx = None
            st.info("Canceled.")

        if confirm:
            wallet = utils.get_wallet(pending["wallet_id"])
            w3, code = get_web3_or_none(pending["network_code"])
            if not wallet or not w3:
                return

            try:
                private_key = utils.decrypt_private_key(wallet["keystore"], password)
            except ValueError as e:
                st.error(f"❌ {e}")
                return

            from_address = Web3.to_checksum_address(wallet["address"])
            to_address = Web3.to_checksum_address(pending["to_address"])
            chain_id = w3.eth.chain_id

            tx = build_native_transfer_tx(w3, chain_id, from_address, to_address, pending["amount_wei"])

            with st.spinner("Signing and broadcasting transaction..."):
                signed_tx = Account.sign_transaction(tx, private_key)
                private_key = None
                tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)

            st.session_state.pending_tx = None
            st.success("✅ Transaction sent.")
            st.code(tx_hash.hex())

def page_networks():
    st.header("🌐 Networks")

    networks = utils.list_networks()
    if networks:
        st.table([
            {"Code": code, "Symbol": utils.NATIVE_SYMBOLS.get(code, code), "RPC URL": url}
            for code, url in networks.items()
        ])
    else:
        st.info("No network configured yet.")

    st.subheader("Add / Update Network")
    with st.form("add_network_form", clear_on_submit=True):
        code = st.text_input("Code (e.g. ETH, POL, BNB, ARB, AVAX)")
        rpc_url = st.text_input("RPC URL")
        submitted = st.form_submit_button("Save Network")

    if submitted:
        try:
            saved_code = utils.add_network(code, rpc_url)
            st.success(f"✅ Network '{saved_code}' saved.")
        except ValueError as e:
            st.error(f"❌ {e}")

    if networks:
        st.subheader("Remove Network")
        code_to_delete = st.selectbox("Select network to remove", list(networks.keys()), key="del_network")
        if st.button("🗑️ Delete Network"):
            if utils.delete_network(code_to_delete):
                st.success(f"✅ Network '{code_to_delete}' removed.")
                st.rerun()

st.sidebar.title("🔐 Wallet Manager")
st.sidebar.caption("Offline - Multi-Chain (EVM)")
page = st.sidebar.radio("Menu", ["Generate Wallet", "Wallets & Balances", "Transfer", "Networks"])

if page == "Generate Wallet":
    page_generate_wallet()
elif page == "Wallets & Balances":
    page_wallets_and_balances()
elif page == "Transfer":
    page_transfer()
elif page == "Networks":
    page_networks()