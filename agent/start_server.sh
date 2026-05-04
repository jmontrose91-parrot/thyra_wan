#!/bin/bash
# Start thyra llama-server once models are ready
set -e

MODEL_DIR="$HOME/models"
QWEN3="$MODEL_DIR/Qwen3-8B-abliterated-Q4_K_M.gguf"
CODER="$MODEL_DIR/Qwen2.5-Coder-7B-abliterated-Q4_K_M.gguf"

QWEN3_MIN=4700000000    # ~4.9GB expected, accept if >= 4.7GB
CODER_MIN=4000000000    # ~4.3GB expected, accept if >= 4.0GB

echo "[thyra] Checking model downloads..."

check_model() {
    local path="$1"
    local min_size="$2"
    local name="$(basename $path)"
    if [ ! -f "$path" ]; then
        echo "  MISSING: $name"
        return 1
    fi
    local size=$(stat -c%s "$path")
    if [ "$size" -lt "$min_size" ]; then
        local pct=$((size * 100 / min_size))
        echo "  PARTIAL: $name (${pct}%, $(numfmt --to=iec $size))"
        return 1
    fi
    echo "  OK: $name ($(numfmt --to=iec $size))"
    return 0
}

check_model "$QWEN3" "$QWEN3_MIN" || { echo "[thyra] Qwen3 not ready, waiting..."; exit 1; }
check_model "$CODER" "$CODER_MIN" || { echo "[thyra] Coder not ready, waiting..."; exit 1; }

echo "[thyra] Both models ready. Starting llama-server..."

# Start the service
echo "Metalcore1!" | sudo -S systemctl start thyra-llama

# Wait for health check
for i in $(seq 1 30); do
    sleep 4
    if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
        echo "[thyra] llama-server ONLINE at http://localhost:8080"
        exit 0
    fi
    echo "  waiting... ($((i*4))s)"
done

echo "[thyra] ERROR: llama-server did not come online in 120s"
echo "Metalcore1!" | sudo -S journalctl -u thyra-llama --no-pager -n 30
exit 1
