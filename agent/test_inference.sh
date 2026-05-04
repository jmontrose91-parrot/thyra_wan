#!/bin/bash
# Test GPU inference for both models
# Run after models are downloaded and llama-server is started.
set -e

export PATH="/usr/local/cuda/bin:$PATH"
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"

LLAMA_CLI="/home/thyra/llama.cpp/build/bin/llama-cli"
MODEL_DIR="/home/thyra/models"
QWEN3="$MODEL_DIR/Qwen3-8B-abliterated-Q4_K_M.gguf"
CODER="$MODEL_DIR/Qwen2.5-Coder-7B-abliterated-Q4_K_M.gguf"

echo "============================================================"
echo " Thyra Inference Test"
echo " GPU: $(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo 'check: /dev/dri/renderD128')"
echo "============================================================"

run_inference_test() {
    local model="$1"
    local prompt="$2"
    local label="$3"
    local min_tps=5  # minimum acceptable tokens/sec

    echo ""
    echo "[TEST] $label"
    echo "  Model: $(basename $model)"
    echo "  Prompt: $prompt"

    local start=$(date +%s%N)
    local output
    output=$(sg render -c "
        export PATH=/usr/local/cuda/bin:\$PATH
        export LD_LIBRARY_PATH=/usr/local/cuda/lib64:\$LD_LIBRARY_PATH
        $LLAMA_CLI \
            -m $model \
            --n-gpu-layers 99 \
            --ctx-size 512 \
            --temp 0.1 \
            -n 50 \
            --no-display-prompt \
            -p '<|im_start|>user\n$prompt<|im_end|>\n<|im_start|>assistant\n'
    " 2>&1)
    local end=$(date +%s%N)
    local elapsed_ms=$(( (end - start) / 1000000 ))
    local elapsed_s=$(( elapsed_ms / 1000 ))

    # Count output tokens (rough estimate: ~4 chars/token)
    local out_len=${#output}
    local est_tokens=$(( out_len / 4 ))
    local tps=0
    [ $elapsed_s -gt 0 ] && tps=$(( est_tokens / elapsed_s ))

    echo "  Output: ${output:0:150}"
    echo "  Time: ${elapsed_s}s | ~${est_tokens} tokens | ~${tps} tok/s"

    if echo "$output" | grep -qi "error\|cuda\|failed\|cannot"; then
        echo "  STATUS: FAIL (error in output)"
        return 1
    fi

    if [ $tps -ge $min_tps ]; then
        echo "  STATUS: PASS (${tps} tok/s >= ${min_tps})"
    else
        echo "  STATUS: WARN (${tps} tok/s — may be CPU-only)"
    fi
}

# Test 1: Server health check
echo ""
echo "[TEST] llama-server health"
if curl -sf http://localhost:8080/health >/dev/null 2>&1; then
    echo "  STATUS: PASS — server online"

    # Test via API
    echo ""
    echo "[TEST] API inference (server)"
    response=$(curl -sf -X POST http://localhost:8080/v1/chat/completions \
        -H "Content-Type: application/json" \
        -d '{"model":"thyra","messages":[{"role":"user","content":"Reply with only: THYRA_ONLINE"}],"max_tokens":10,"temperature":0}')
    if echo "$response" | grep -q "THYRA_ONLINE"; then
        echo "  STATUS: PASS — API responding correctly"
    else
        echo "  STATUS: WARN — unexpected response: ${response:0:100}"
    fi
else
    echo "  STATUS: FAIL — server not running"
    echo "  Run: sudo systemctl start thyra-llama"
fi

# Test 2: Direct GPU inference
if [ -f "$QWEN3" ]; then
    run_inference_test "$QWEN3" "List 3 nmap flags for port scanning" "Qwen3-8B GPU inference"
else
    echo ""
    echo "[SKIP] Qwen3 model not found: $QWEN3"
fi

echo ""
echo "============================================================"
echo " Test complete"
echo "============================================================"
