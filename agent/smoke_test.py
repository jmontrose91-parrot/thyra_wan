"""
Thyra WAN Smoke Test
Run: python3 smoke_test.py
Tests all components without requiring LLM inference.
"""

import sys
import os
import json
import subprocess
import time

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
WARN = "\033[33mWARN\033[0m"
results = []


def check(name, ok, detail="", optional=False):
    if ok:
        tag = PASS
    elif optional:
        tag = WARN
    else:
        tag = FAIL
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    results.append((name, ok, optional))
    return ok


def section(title):
    print(f"\n{'='*50}\n  {title}\n{'='*50}")


# ── IMPORTS ──────────────────────────────────────────────────────────────────
section("1. Module Imports")

try:
    from commands.vocabulary import COMMANDS, match_command, list_commands
    check("vocabulary module", True, f"{len(COMMANDS)} commands")
except Exception as e:
    check("vocabulary module", False, str(e))

try:
    from prompts.system_prompts import INSTRUCT_SYSTEM, CODER_SYSTEM, WORKFLOW_CONTEXT
    check("prompts module", True, f"{len(WORKFLOW_CONTEXT)} workflows")
except Exception as e:
    check("prompts module", False, str(e))

try:
    from tools.executor import run_tool, extract_commands, save_finding, init_db, get_timeout
    check("executor module", True)
except Exception as e:
    check("executor module", False, str(e))

try:
    import dorking_filter
    check("dorking_filter module", True)
except Exception as e:
    check("dorking_filter module", False, str(e))

try:
    import react_loop
    check("react_loop module", True)
except Exception as e:
    check("react_loop module", False, str(e))


# ── VOCABULARY MATCHING ───────────────────────────────────────────────────────
section("2. Vocabulary Matching")

from commands.vocabulary import match_command

test_cases = [
    ("port scan 192.168.1.1", "port_scan"),
    ("full recon example.com", "full_recon"),
    ("scan wifi", "wifi_survey"),
    ("sniff traffic eth0", "packet_capture"),
    ("rf sweep 100M-500M", "spectrum_scan"),
    ("subdomain enum google.com", "subdomain_scan"),
    ("osint 192.168.1.5", "recon"),
    ("433 scan", "iot433"),
    ("ads-b", "aircraft_scan"),
    ("dns recon target.com", "dns_recon"),
    ("dir fuzz http://target.com", "dir_fuzz"),
    ("network map 192.168.1.0/24", "network_map"),
    # new commands
    ("recon-ng example.com", "recon_ng"),
    ("full osint target.org", "recon_ng"),
    ("kismet survey wlan0", "kismet_survey"),
    ("passive wifi", "kismet_survey"),
    ("power scan 88M:108M", "rtl_power_scan"),
    ("signal survey", "rtl_power_scan"),
    ("lora scan", "lora_scan"),
    ("meshtastic scan", "lora_scan"),
    # disambiguation — must NOT match shorter alias
    ("rf survey", "rf_survey"),            # NOT spectrum_scan
    ("hackrf sweep 100:500", "hackrf_scan"),    # hackrf sweep -> dedicated hackrf_scan command
]

for text, expected in test_cases:
    name, _ = match_command(text)
    check(f'  "{text}"', name == expected, f"got {name}, want {expected}")


# ── COMMAND EXTRACTION ────────────────────────────────────────────────────────
section("3. Command Extraction")

from tools.executor import extract_commands

samples = [
    ("```\nnmap -sV 192.168.1.1\n```", ["nmap -sV 192.168.1.1"]),
    ("1. nmap -sV target\n2. tshark -i eth0", ["nmap -sV target", "tshark -i eth0"]),
    ("Run `nmap -p 80 target` to check.", ["nmap -p 80 target"]),
]

for sample, expected in samples:
    got = extract_commands(sample)
    check(f"  extract {repr(sample[:30])}", got == expected, f"got {got}")


# ── DATABASE ──────────────────────────────────────────────────────────────────
section("4. SQLite Database")

try:
    conn = init_db()
    conn.execute("SELECT count(*) FROM findings").fetchone()
    check("DB init + query", True)
    conn.close()
except Exception as e:
    check("DB init + query", False, str(e))

try:
    save_finding("test_tool", "echo test", "localhost", "test output", "smoke test")
    check("save_finding", True)
except Exception as e:
    check("save_finding", False, str(e))


# ── TOOL EXECUTION ────────────────────────────────────────────────────────────
section("5. Tool Execution")

result = run_tool("echo thyra_test", target="test", timeout=5)
check("echo command", result["success"] and result["output"] == "thyra_test")

result = run_tool("nmap --version", target="test", timeout=10)
check("nmap --version", result["success"], result["output"][:40] if result["success"] else result["output"][:80])

result = run_tool("tshark --version", target="test", timeout=10)
check("tshark --version", result["success"], result["output"][:40] if result["success"] else result["output"][:80])

result = run_tool("gobuster --help 2>&1 | head -1", target="test", timeout=10)
check("gobuster --help", result["success"] or "Usage" in result["output"])

result = run_tool("rtl_433 --help 2>&1 | head -1", target="test", timeout=5)
check("rtl_433 help", result["success"] or result["returncode"] == 1)

result = run_tool("nikto -H 2>&1 | head -1", target="test", timeout=10)
check("nikto help", result["success"] or "Options" in result["output"] or result["returncode"] in (0, 1))


# ── INSTALLED TOOLS ───────────────────────────────────────────────────────────
section("6. Tool Availability")

tools = {
    "nmap": "which nmap",
    "masscan": "which masscan",
    "tshark": "which tshark",
    "aircrack-ng": "which aircrack-ng",
    "airodump-ng": "which airodump-ng",
    "rtl_433": "which rtl_433",
    "dump1090-mutability": "which dump1090-mutability",
    "gobuster": "which gobuster",
    "ffuf": "which ffuf",
    "nikto": "which nikto",
    "sqlmap": "which sqlmap",
    "hping3": "which hping3",
    "dnsrecon": "which dnsrecon",
    "hydra": "which hydra",
    "recon-ng": "which recon-ng",
    "p0f": "which p0f",
    "whois": "which whois",
    "dig": "which dig",
}
optional_tools = {
    "theHarvester": "which theHarvester",
    "hackrf_sweep": "which hackrf_sweep",
    "hackrf_transfer": "which hackrf_transfer",
    "rtl_sdr": "which rtl_sdr",
    "kismet": "which kismet",
    "csdr": "which csdr",
    "netdiscover": "which netdiscover",
}

for name, cmd in tools.items():
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    check(f"  {name}", r.returncode == 0,
          r.stdout.strip() if r.returncode == 0 else "NOT FOUND")

for name, cmd in optional_tools.items():
    r = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    check(f"  {name} (optional)", r.returncode == 0,
          r.stdout.strip() if r.returncode == 0 else "NOT FOUND",
          optional=True)


# ── PYTHON TOOL MODULES ───────────────────────────────────────────────────────
section("6b. Python Tool Modules")

try:
    from tools.device_finder import find_pinpulse, find_heltec, list_devices
    check("tools.device_finder", True)
    devs = list_devices()
    pinpulse = devs["pinpulse"]
    heltec   = devs["heltec_lora"]
    check("  PinPulse Shield (ESP32S3_DEV)", pinpulse is not None,
          pinpulse or "not connected", optional=True)
    check("  Heltec LoRa 32 V4 (heltec_wifi_lora_32_v4)", heltec is not None,
          heltec or "not connected", optional=True)
except Exception as e:
    check("tools.device_finder", False, str(e))

try:
    from tools.rtl_power_json import rtl_power_to_json, top_signals
    check("tools.rtl_power_json", True)
except Exception as e:
    check("tools.rtl_power_json", False, str(e))

try:
    from tools.hackrf_sdr import sweep_cli, top_signals as hackrf_top
    check("tools.hackrf_sdr", True)
except Exception as e:
    check("tools.hackrf_sdr", False, str(e))

try:
    import python_hackrf
    check("  pip: python_hackrf", True, optional=True)
except (ImportError, ValueError, Exception) as e:
    check("  pip: python_hackrf", False, f"pip3 install python_hackrf  [{e}]", optional=True)

try:
    from tools.kismet_client import get_devices, start_kismet_server
    check("tools.kismet_client", True)
except Exception as e:
    check("tools.kismet_client", False, str(e))

try:
    from tools.lora_listener import listen_meshtastic, listen_serial_raw
    check("tools.lora_listener", True)
except Exception as e:
    check("tools.lora_listener", False, str(e))

try:
    import meshtastic
    check("  pip: meshtastic", True, meshtastic.__version__ if hasattr(meshtastic, "__version__") else "ok", optional=True)
except ImportError:
    check("  pip: meshtastic", False, "pip3 install meshtastic", optional=True)

try:
    import kismet_rest
    check("  pip: kismet-rest", True, optional=True)
except ImportError:
    check("  pip: kismet-rest", False, "pip3 install kismet-rest", optional=True)

try:
    import rtlsdr
    check("  pip: pyrtlsdr", True, optional=True)
except (ImportError, AttributeError, OSError) as e:
    # AttributeError/OSError: librtlsdr.so may be older than pyrtlsdr expects
    check("  pip: pyrtlsdr", False, f"librtlsdr compat issue: {e}", optional=True)

try:
    from tools.esp32_controller import send_command, wifi_scan, deauth, ble_scan
    check("tools.esp32_controller", True)
    result = send_command("status", timeout=5)
    if result.get("success") and result.get("data", {}).get("version") == "1.0":
        check("  ESP32 PinPulse — serial comms", True,
              f"port={result.get('port')} heap={result['data'].get('heap',0):,}")
    else:
        check("  ESP32 PinPulse — serial comms", False,
              result.get("error", result.get("raw", "not connected")), optional=True)
except Exception as e:
    check("tools.esp32_controller", False, str(e))


# ── LLAMA SERVER ──────────────────────────────────────────────────────────────
section("7. LLaMA Server")

import urllib.request
try:
    req = urllib.request.Request("http://localhost:8080/health")
    with urllib.request.urlopen(req, timeout=3) as resp:
        data = json.loads(resp.read())
        check("llama-server /health", True, str(data))
except Exception as e:
    check("llama-server /health", False, str(e))

import os
from pathlib import Path
models_dir = Path.home() / "models"
# Qwen3-8B-abliterated-Q4_K_M: ~5.4GB; Qwen2.5-Coder-7B-abliterated: ~4.0GB
model_specs = [
    ("Qwen3-8B-abliterated-Q4_K_M.gguf",       4.7),
    ("Qwen2.5-Coder-7B-abliterated-Q4_K_M.gguf", 3.8),
]
for model, min_gb in model_specs:
    p = models_dir / model
    if p.exists():
        size_gb = p.stat().st_size / 1e9
        complete = size_gb >= min_gb
        check(f"  model {model[:35]}", complete,
              f"{size_gb:.2f}GB {'(complete)' if complete else '(downloading...)'}")
    else:
        check(f"  model {model[:35]}", False, "NOT FOUND")


# ── SUMMARY ───────────────────────────────────────────────────────────────────
section("SUMMARY")
passed = sum(1 for _, ok, opt in results if ok)
required_total = sum(1 for _, _, opt in results if not opt)
required_passed = sum(1 for _, ok, opt in results if ok and not opt)
pct = 100 * passed // len(results) if results else 0
print(f"\n  {passed}/{len(results)} checks passed ({pct}%)")
print(f"  Required: {required_passed}/{required_total}")
failed_required = [(n, ok, opt) for n, ok, opt in results if not ok and not opt]
if failed_required:
    print("\n  Failed (required):")
    for name, ok, opt in failed_required:
        print(f"    - {name}")
warned = [(n, ok, opt) for n, ok, opt in results if not ok and opt]
if warned:
    print("\n  Warnings (optional):")
    for name, ok, opt in warned:
        print(f"    - {name}")
print()
sys.exit(0 if required_passed == required_total else 1)
