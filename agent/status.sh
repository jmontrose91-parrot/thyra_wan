#!/bin/bash
# Quick Thyra system status report
# Usage: thyra_status  (or: bash ~/agent/status.sh)

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "  [${GREEN}OK${NC}]  $1"; }
fail() { echo -e "  [${RED}FAIL${NC}] $1"; }
warn() { echo -e "  [${YELLOW}WARN${NC}] $1"; }

echo "========================================"
echo "  THYRA WAN — System Status"
echo "========================================"

# GPU
echo ""
echo "[GPU]"
if command -v nvidia-smi >/dev/null 2>&1; then
    nvidia-smi --query-gpu=name,memory.total,memory.used,memory.free,temperature.gpu \
        --format=csv,noheader 2>/dev/null | while IFS=, read name total used free temp; do
        echo "  $name"
        echo "  VRAM: $total total | $used used | $free free"
        echo "  Temp: $temp"
    done
else
    vram=$(cat /proc/driver/nvidia/params 2>/dev/null | grep -i vram | head -1)
    if [ -z "$vram" ]; then
        warn "nvidia-smi not found — check render group"
    fi
fi

# Models
echo ""
echo "[Models]"
MODEL_DIR="$HOME/models"
for model in Qwen3-8B-abliterated-Q4_K_M.gguf Qwen2.5-Coder-7B-abliterated-Q4_K_M.gguf; do
    path="$MODEL_DIR/$model"
    if [ -f "$path" ]; then
        size=$(du -sh "$path" | cut -f1)
        ok "$model ($size)"
    else
        fail "$model — NOT FOUND"
    fi
done

# LLM Server
echo ""
echo "[LLM Server]"
if systemctl is-active --quiet thyra-llama 2>/dev/null; then
    ok "thyra-llama.service RUNNING"
else
    warn "thyra-llama.service stopped (run: sudo systemctl start thyra-llama)"
fi
if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
    ok "llama-server API responding at localhost:8080"
else
    warn "llama-server not responding"
fi

# Disk
echo ""
echo "[Disk]"
df -h / | tail -1 | awk '{printf "  Root: %s used / %s total (%s)\n", $3, $2, $5}'
df -h /tmp | tail -1 | awk '{printf "  /tmp: %s used / %s total\n", $3, $2}'

# Findings DB
echo ""
echo "[Findings DB]"
if [ -f "$HOME/findings.db" ]; then
    count=$(sqlite3 "$HOME/findings.db" "SELECT count(*) FROM findings;" 2>/dev/null)
    size=$(du -sh "$HOME/findings.db" | cut -f1)
    ok "findings.db: $count entries ($size)"
else
    warn "findings.db not created yet (run a scan first)"
fi

# Services
echo ""
echo "[Services]"
for svc in ssh vnc@:1; do
    port=$(echo $svc | grep -oE "[0-9]+")
    if netstat -tnl 2>/dev/null | grep -q ":${port:-22} "; then
        ok "$svc open"
    fi
done
ss -tnl 2>/dev/null | grep -qE ":22 " && ok "SSH (22)" || warn "SSH not listening"
ss -tnl 2>/dev/null | grep -qE ":5901 " && ok "VNC (5901)" || warn "VNC not on 5901"
ss -tnl 2>/dev/null | grep -qE ":8080 " && ok "llama-server (8080)" || warn "llama-server not on 8080"

echo ""
echo "========================================"
echo "  Quick commands:"
echo "  thyra help           — command list"
echo "  thyra findings       — view scan DB"
echo "  thyra smoke          — run self-tests"
echo "  thyra server         — start LLM server"
echo "  thyra agent <task>   — run ReAct agent"
echo "========================================"
