# Thyra WAN

**Portable SIGINT/OSINT AI cyberdeck.** Apache 1800 case housing a Jetson Orin Nano running a local LLM agent that orchestrates security tools via CLI in a ReAct loop (Thought → Action → Observe → Report).

---

## Hardware

| Component | Status |
|---|---|
| Jetson Orin Nano Dev Kit | Running — SSH + VNC configured |
| HackRF One | On hand — needs antennas |
| ESP32-S3 PinPulse Shield | On hand — Marauder not yet flashed |
| Heltec WiFi LoRa 32 V4 | On hand — Meshtastic not yet flashed |
| NullLab RF-Nano | On hand |
| Apache 1800 case | On hand |
| Elecrow 7" LCD Display-C | On hand |
| Doohoeek mini keyboard X004L62PJJ | On hand |

## Software Stack (on Jetson)

- **OS:** JetPack 6.2.1 (Ubuntu 22.04, CUDA 12.6)
- **LLM:** llama.cpp with CUDA (SM 8.7), models at `~/models/`
  - Qwen3-8B-Q4_K_M.gguf — reasoning/agent slot
  - Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf — code/command slot
- **Tools:** nmap, masscan, tshark, aircrack-ng, rtl-sdr, rtl-433, gnuradio, nikto, sqlmap, ffuf, gobuster, jq, tmux, sqlite3, ripgrep, theharvester, dnsrecon

## Access

| Method | Address | Credentials |
|---|---|---|
| SSH (USB-C) | `thyra@192.168.55.1` | `Metalcore1!` |
| VNC | `192.168.55.1:5901` | `thyra123` |

Run GPU inference: `sg render -c '~/llama.cpp/build/bin/llama-cli -m ~/models/Qwen3-8B-Q4_K_M.gguf --n-gpu-layers 99 ...'`

---

## GitHub Issues

- [#1 — Shopping List](../../issues/1)
- [#2 — Case Design & Layout](../../issues/2)
- [#3 — Software Remaining Tasks](../../issues/3)

---

## Handoff Prompt (for mobile agents / new sessions)

> You are continuing build work on **Thyra WAN** — a SIGINT/OSINT cyberdeck in an Apache 1800 case.
>
> **Repo:** https://github.com/jmontrose91-parrot/thyra_wan
> Read issues #1 (shopping list), #2 (case design), #3 (software tasks) before starting.
>
> **Jetson Orin Nano** is running and accessible:
> - SSH: `thyra@192.168.55.1` password `Metalcore1!`
> - VNC: `192.168.55.1:5901` password `thyra123`
> - Connected via USB-C gadget networking
>
> **Current software state:**
> - llama.cpp built with CUDA at `~/llama.cpp/build/bin/`
> - Models: `~/models/Qwen3-8B-Q4_K_M.gguf` + `~/models/Qwen2.5-Coder-7B-Instruct-Q4_K_M.gguf`
> - GPU: 7619MB VRAM (SM 8.7 Ampere) — use `sg render -c '...'` for GPU access
> - Security tools installed (see issue #3)
>
> **Immediate next tasks** (pick up from issue #3):
> 1. Add swap file (4GB)
> 2. Create llama-server systemd service
> 3. Flash ESP32-S3 with Marauder
> 4. Build Python ReAct agent framework
>
> **Case design** (issue #2): Apache 1800, 8.125"×5.625"×3.75" internal. Keyboard in lid, display + Jetson + HackRF in body. ⚠️ Verify keyboard dimensions (reported 9" may exceed 8.125" case width).
