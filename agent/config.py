"""
Thyra WAN — Central Configuration
Edit this file to tune paths, model settings, and server options.
"""
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────────────
HOME          = Path.home()
AGENT_DIR     = HOME / "agent"
MODEL_DIR     = HOME / "models"
LOG_DIR       = HOME / "logs"
OUTPUT_DIR    = Path("/tmp/thyra_output")
DB_PATH       = HOME / "findings.db"

LOG_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# ── Models ────────────────────────────────────────────────────────────────────
INSTRUCT_MODEL = str(MODEL_DIR / "Qwen3-8B-abliterated-Q4_K_M.gguf")
CODER_MODEL    = str(MODEL_DIR / "Qwen2.5-Coder-7B-abliterated-Q4_K_M.gguf")
LLAMA_CLI      = str(HOME / "llama.cpp/build/bin/llama-cli")

# ── Server ────────────────────────────────────────────────────────────────────
LLAMA_SERVER   = "http://localhost:8080"
SERVER_TIMEOUT = 120      # seconds to wait for server response
GPU_LAYERS     = 99       # -1 = all layers on GPU
CTX_SIZE       = 4096
TEMP           = 0.3      # low temp for reliable command generation
MAX_TOKENS     = 1024

# ── Agent ─────────────────────────────────────────────────────────────────────
MAX_ITERATIONS = 6        # ReAct loop max rounds
OBS_CONTEXT    = 3        # how many previous observations to include
TOOL_OUTPUT_LIMIT = 500   # chars of tool output to feed back into context
DB_RESULT_LIMIT   = 4096  # chars to store in findings DB per entry

# ── Hardware ──────────────────────────────────────────────────────────────────
HACKRF_GAIN_LNA = 32      # LNA gain (0-40 dB, step 8)
HACKRF_GAIN_VGA = 32      # VGA gain (0-62 dB, step 2)
HACKRF_SAMPLE_RATE = 20e6 # 20 MSPS default

RTL_GAIN   = 40           # RTL-SDR gain (dB)
RTL_SAMPLE = 250000       # RTL sample rate for rtl_433

MESHTASTIC_PORT = "/dev/ttyUSB0"   # adjust if Heltec is on different port
MESHTASTIC_BAUD = 115200

WIFI_MONITOR_IF = "wlan0"          # base interface; mon = wlan0mon after airmon-ng
ESP32_PORT      = "/dev/ttyUSB1"   # Marauder ESP32-S3

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL  = "INFO"   # DEBUG, INFO, WARNING, ERROR
LOG_FILE   = LOG_DIR / "thyra.log"
LOG_MAX_MB = 10
LOG_BACKUPS = 3
