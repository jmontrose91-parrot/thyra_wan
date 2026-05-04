#!/bin/bash
# Thyra WAN agent setup — run once on Jetson
set -e

AGENT_DIR="$HOME/agent"
mkdir -p "$AGENT_DIR" "$HOME/logs" "$HOME/models" "$HOME/.local/bin"

# ── Copy agent files ──────────────────────────────────────────────────────────
if [ -d "/tmp/thyra_agent" ]; then
    cp -r /tmp/thyra_agent/* "$AGENT_DIR/"
    echo "[setup] Agent files copied"
fi

# ── Python dependencies ───────────────────────────────────────────────────────
echo "[setup] Installing Python deps..."
pip3 install requests rich openai sqlite-utils meshtastic kismet-rest pyrtlsdr 2>/dev/null || true

# python_hackrf — preferred HackRF Python binding (requires libhackrf >= 2024.02.1)
sudo apt-get install -y libusb-1.0-0-dev 2>/dev/null || true
pip3 install python_hackrf 2>/dev/null || true

# ── Security tools ────────────────────────────────────────────────────────────
echo "[setup] Installing security tools..."
sudo apt-get install -y \
    nmap masscan tshark aircrack-ng airodump-ng \
    rtl-433 dump1090-mutability gobuster ffuf \
    nikto sqlmap hping3 dnsrecon hydra \
    recon-ng p0f netdiscover \
    2>/dev/null || true

# ── Kismet (official repo — Ubuntu 22.04 jammy arm64) ─────────────────────────
echo "[setup] Installing Kismet..."
if ! command -v kismet &>/dev/null; then
    wget -q -O /tmp/kismet.gpg https://www.kismetwireless.net/repos/kismet-release.gpg.key \
        && cat /tmp/kismet.gpg | gpg --dearmor | sudo tee /usr/share/keyrings/kismet-archive-keyring.gpg >/dev/null \
        && echo 'deb [signed-by=/usr/share/keyrings/kismet-archive-keyring.gpg] https://www.kismetwireless.net/repos/apt/release/jammy jammy main' \
           | sudo tee /etc/apt/sources.list.d/kismet.list \
        && sudo apt-get update -qq \
        && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y kismet \
        && sudo usermod -aG kismet "$USER" \
        && echo "[setup] Kismet installed" \
        || echo "[WARN] Kismet install failed — run 'thyra smoke' for details"
else
    echo "[setup] Kismet already installed"
fi

# ── llama-server systemd service ──────────────────────────────────────────────
if [ -f "$AGENT_DIR/llama_server.service" ]; then
    sudo cp "$AGENT_DIR/llama_server.service" /etc/systemd/system/thyra-llama.service
    sudo systemctl daemon-reload
    sudo systemctl enable thyra-llama.service
    echo "[setup] thyra-llama service registered"
fi

# ── Swap (4GB) ────────────────────────────────────────────────────────────────
if ! swapon --show | grep -q /swapfile; then
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "[setup] 4GB swap created"
fi

# ── thyra CLI wrapper ──────────────────────────────────────────────────────────
cat > "$HOME/.local/bin/thyra" << 'WRAPPER'
#!/bin/bash
cd ~/agent
case "$1" in
    findings) shift; python3 view_findings.py "$@" ;;
    agent)    shift; python3 react_loop.py "$@" ;;
    smoke)    python3 smoke_test.py ;;
    test)     ~/agent/test_inference.sh ;;
    server)   ~/agent/start_server.sh ;;
    status)   ~/agent/status.sh ;;
    *)        python3 dorking_filter.py "$@" ;;
esac
WRAPPER
chmod +x "$HOME/.local/bin/thyra"

grep -q 'local/bin' "$HOME/.bashrc" || echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"

echo ""
echo "[setup] ── Complete ──────────────────────────────────────────────────────"
echo "[setup] Start server:   thyra server"
echo "[setup] Run smoke test: thyra smoke"
echo "[setup] Interactive:    thyra"
echo ""
echo "[NOTE] If Kismet was just installed, log out and back in (kismet group)."
