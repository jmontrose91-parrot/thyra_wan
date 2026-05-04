#!/bin/bash
# Run this ON THE JETSON to authorize the Parrot laptop's SSH key.
# After running, the Parrot machine can SSH in without a password.
set -e

PUBKEY="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIAvisW3I8zSyE/rA9QrpUhhn9Yv8YZFCocd1oy/HByD1 odin@parrot"

mkdir -p ~/.ssh
chmod 700 ~/.ssh
touch ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

if grep -qF "$PUBKEY" ~/.ssh/authorized_keys 2>/dev/null; then
    echo "[auth] Key already authorized."
else
    echo "$PUBKEY" >> ~/.ssh/authorized_keys
    echo "[auth] Key added to authorized_keys."
fi

echo "[auth] Done. You can now SSH from the Parrot laptop without a password."
