#!/bin/bash
# Thyra WAN agent setup — run once on Jetson as thyra user
set -e

AGENT_DIR="$HOME/agent"
mkdir -p "$AGENT_DIR"

# Copy agent files
cp -r /tmp/thyra_agent/* "$AGENT_DIR/" 2>/dev/null || true

# Install Python deps
pip3 install --break-system-packages requests rich openai sqlite-utils 2>/dev/null || true

# Install llama-server systemd service
sudo cp "$AGENT_DIR/llama_server.service" /etc/systemd/system/thyra-llama.service
sudo systemctl daemon-reload
sudo systemctl enable thyra-llama.service

# Add swap if not present
if ! swapon --show | grep -q /swapfile; then
    sudo fallocate -l 4G /swapfile
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
    echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    echo "[setup] Swap created"
fi

# Create thyra CLI wrapper
cat > "$HOME/.local/bin/thyra" << 'WRAPPER'
#!/bin/bash
cd ~/agent
python3 dorking_filter.py "$@"
WRAPPER
chmod +x "$HOME/.local/bin/thyra"
mkdir -p "$HOME/.local/bin"
echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"

echo "[setup] Done. Start llama-server: sudo systemctl start thyra-llama"
echo "[setup] Then run: thyra"
