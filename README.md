# Wallet Manager (Offline - Multi-Chain)

Offline-style management of EVM wallets (Ethereum, Polygon, BSC and any other EVM-compatible network) with encrypted private keys (standard Ethereum Keystore v3 format - the same as MetaMask and Geth).

Since all of these networks are EVM-compatible, *one wallet (one address + one key)* works on all of them, you just choose the network you want when checking balances or transferring.

The app is a single **Streamlit** interface (`app.py`) backed by a local **SQLite** database (`wallets.db`). Wallets and networks are managed entirely from the UI - no manual file editing needed.

## Install

```bash
cd Wallet
pip install streamlit web3
```

## Run

```bash
streamlit run app.py
```

This opens the app in your browser (by default at `http://localhost:8501`). On first run, it automatically creates `wallets.db` in the project folder to store networks and encrypted wallets.

## Usage

The app has four pages, selectable from the sidebar:

### 🌐 Networks
Add the RPC URL for each network you want to use, with a short code (e.g. `ETH`, `POL`, `BNB`, `ARB`, `AVAX`):

```
ETH  -> https://ethereum-rpc.publicnode.com
POL  -> https://polygon-rpc.com
BNB  -> https://bsc-dataseed.binance.org
```

You can add, update, or remove as many networks as you want at any time. The code is just a display tag and is recognized automatically everywhere else in the app.

### 🆕 Generate Wallet
Enter and confirm a password. The app creates a new wallet, encrypts the private key (Keystore v3) with that password, and stores the address + encrypted key in `wallets.db`. This wallet can be used on all EVM networks.

### 💼 Wallets & Balances
Shows all saved wallets. Pick a network and click "Refresh Balances" to display the balance of every wallet on that network.

### 🔁 Transfer
Pick the network, the sender wallet, the recipient address, and the amount. Click "Prepare Transaction" to review the details, then enter your password to decrypt the private key in memory, sign, and broadcast the transaction. You can cancel before confirming.

## Important Security Tips

1. **Never put `wallets.db` in Git, the cloud, or any online service.** It contains your encrypted private keys.
2. Keep an **offline** backup of `wallets.db` (on an encrypted USB, e.g. with VeraCrypt).
3. Keep the password you choose to encrypt your keys in a safe place (not on the same system); without it, there is no way to recover the private key.
4. Run the app only on `localhost`. If you ever need remote access, put it behind HTTPS and proper authentication - Streamlit itself has no built-in login.
5. For large amounts, a hardware wallet (Ledger/Trezor) is a more secure option than any software method.
6. Run this app on a system you trust (no malware/keyloggers).