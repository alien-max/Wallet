# Wallet Manager (Offline - Multi-Chain)

Offline management of EVM wallets (Ethereum, Polygon, BSC and any other EVM-compatible network) with encrypted private key (standard Ethereum Keystore v3 format - the same as MetaMask and Geth).

Since all of these networks are EVM-compatible, *one wallet (one address + one key)* works on all of them, you just choose the network you want when receiving balance or transferring.

## Install

```bash
cd Wallet
pip install -r requirements.txt
cp .env.example .env
```

Then, in the `.env` file, for each network you want to use, add a line with the following format:

```
ETH_RPC_URL=https://ethereum-rpc.publicnode.com
POL_RPC_URL=https://polygon-rpc.com
BNB_RPC_URL=https://bsc-dataseed.binance.org
```

You can add or remove as many networks as you want (e.g. `ARB_RPC_URL` for Arbitrum or `AVAX_RPC_URL` for Avalanche). The three/four letter code before `_RPC_URL` is just a display tag and will be automatically recognized by scripts.

## Usage

### Create new wallet
```bash
python generator.py
```
It will ask you for a password, create a new wallet, and store the address + encrypted key in `.env`. This wallet can be used on all EVM networks.

### Show balance
```bash
python balance.py
```
It first shows the list of networks defined in `.env` and asks you to select one, then displays the balance of all the wallets on that network.

### Transfer assets
```bash
python transfer.py
```
First, the network asks for the source wallet number, destination address, value, and finally the password to temporarily decrypt the private key in memory.

## Important Security Tips

1. **Never put the `.env` file in Git, the cloud, or any online service.**
2. Keep an **offline** backup of the `.env` file (on an encrypted USB, e.g. with VeraCrypt).
3. Keep the password you choose to encrypt your keys in a safe place (not on the same system); without it, there is no way to recover the private key.
4. For large amounts, a hardware wallet (Ledger/Trezor) is a more secure option than any software method.
5. Run these scripts on a system you trust (no malware/keyloggers).