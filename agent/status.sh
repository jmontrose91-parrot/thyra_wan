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
echo "  Orin (nvgpu)"
# tegrastats gives one-shot GPU/RAM stats on Jetson
if command -v tegrastats >/dev/null 2>&1; then
    stats=$(timeout 2 tegrastats --interval 1000 2>/dev/null | head -1)
    ram=$(echo "$stats" | grep -oP 'RAM \K[^(]+' | xargs)
    gpu_util=$(echo "$stats" | grep -oP 'GR3D_FREQ \K[0-9]+')
    cpu_temp=$(echo "$stats" | grep -oP 'CPU@\K[0-9.]+')
    [ -n "$ram" ] && echo "  RAM: $ram" || echo "  RAM: (tegrastats unavailable in session)"
    [ -n "$gpu_util" ] && echo "  GPU util: ${gpu_util}%"
    [ -n "$cpu_temp" ] && echo "  Temp: ${cpu_temp}°C"
else
    warn "tegrastats not found"
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

# Hardware / RF devices
echo ""
echo "[RF Hardware]"
lsusb 2>/dev/null | grep -qi "hackrf" && ok "HackRF One detected" || warn "HackRF not detected (check USB)"
lsusb 2>/dev/null | grep -qi "0bda:2838\|realtek.*rtl" && ok "RTL-SDR detected" || warn "RTL-SDR not detected"
ls /dev/ttyUSB* /dev/ttyACM* 2>/dev/null | while read dev; do
    ok "Serial: $dev"
done

# Services / Ports
echo ""
echo "[Ports]"
for port_label in "22:SSH" "80:lighttpd/dump1090" "5901:VNC" "8080:llama-server" "2501:Kismet REST API"; do
    port="${port_label%%:*}"
    label="${port_label#*:}"
    if ss -tnlp 2>/dev/null | grep -q ":${port} "; then
        ok "${label} (${port})"
    fi
done
ss -tnlp 2>/dev/null | grep -q ":22 " || warn "SSH (22) not listening"

# Recent logs
echo ""
echo "[Logs]"
logfile="$HOME/logs/thyra.log"
if [ -f "$logfile" ]; then
    size=$(du -sh "$logfile" | cut -f1)
    ok "thyra.log exists ($size)"
    echo ""
    tail -5 "$logfile" 2>/dev/null | sed 's/^/    /'
else
    warn "No log yet — log appears on first scan"
fi

echo ""
echo "========================================"
echo "  Quick commands:"
echo "  thyra help           — command list"
echo "  thyra findings       — view scan DB"
echo "  thyra smoke          — run self-tests"
echo "  thyra server         — start LLM server"
echo "  thyra agent <task>   — run ReAct agent"
echo "========================================"
