# Hardware Reference

## Jetson Orin Nano

| Spec | Value |
|---|---|
| SoC | NVIDIA Orin (Ampere, SM 8.7) |
| CPU | 6-core Cortex-A78AE |
| GPU | 1024 CUDA cores, 7619 MB unified VRAM |
| RAM | 8 GB LPDDR5 (shared CPU+GPU) |
| Storage | 64 GB SD card (boot) |
| OS | JetPack 6.2.1 / Ubuntu 22.04 aarch64 |
| CUDA | 12.6 |

### Connections
- **USB-C** → gadget Ethernet `192.168.55.1` (always works when cabled)
- **Ethernet** → DHCP on your network
- **WiFi** → via Alfa adapter (wlan0) when inserted
- **USB-A ports** → HackRF, RTL-SDR, Heltec LoRa, ESP32-S3

---

## Attached Hardware

### HackRF One
- **Role:** Broadband SDR transmitter/receiver, 1 MHz – 6 GHz
- **USB:** auto-detects, confirm with `lsusb | grep HackRF`
- **Tools:** `hackrf_sweep`, `hackrf_transfer`, `hackrf_info`, `python_hackrf`
- **Agent commands:** `hackrf sweep <start_mhz> <end_mhz>`
- **Antennas:** ANT500 for wideband, 2.4 GHz stub for WiFi/BT band, 915 MHz whip for LoRa band

### RTL-SDR
- **Role:** Receive-only SDR, 500 kHz – 1.75 GHz
- **Tools:** `rtl_433`, `rtl_power`, `rtl_sdr`, `dump1090-mutability`
- **Agent commands:** `433 scan`, `aircraft scan`, `fm scan`, `power scan`

### Alfa AWUS036ACH (wlan0)
- **Role:** Monitor-mode WiFi, 2.4 + 5 GHz dual-band
- **Driver:** rtl88xxau (built-in on JetPack)
- **Agent commands:** `scan wifi`, `capture handshake`, `wifi clients`
- **Note:** Plug in before running WiFi commands. `airmon-ng start wlan0` → `wlan0mon`

### Heltec WiFi LoRa 32 V4
- **Role:** LoRa/Meshtastic mesh node, 863–928 MHz
- **Serial:** `/dev/ttyUSB0` (115200 baud)
- **Firmware:** Meshtastic
- **Agent commands:** `lora scan`
- **Status:** `minicom -D /dev/ttyUSB0 -b 115200` to view live output

### ESP32-S3 PinPulse Shield
- **Role:** Active WiFi/BT operations (Marauder firmware)
- **Serial:** `/dev/ttyUSB1` (115200 baud)
- **Firmware:** Marauder
- **Flash:** `esptool.py --port /dev/ttyUSB1 write_flash ...`

### NullLab RF-Nano
- **Role:** MouseJack / nRF24L01 2.4 GHz keyboard/mouse sniffing
- **Serial:** `/dev/ttyUSB*` (varies)

---

## Checking Hardware

```bash
# All USB devices
lsusb

# SDR devices
rtl_433 -h 2>&1 | head -3   # RTL-SDR
hackrf_info                   # HackRF One

# Serial ports (LoRa, ESP32)
ls /dev/ttyUSB* /dev/ttyACM*

# GPU / CUDA
nvidia-smi  (or: cat /sys/bus/platform/drivers/nvgpu/*/vbios_version)
```

---

## Antenna Map

| Connector | Antenna | Frequency |
|---|---|---|
| HackRF SMA | ANT500 | 75 MHz – 1 GHz wideband |
| HackRF SMA | 2.4 GHz stub | WiFi, BT, Zigbee |
| RTL-SDR SMA | 915 MHz whip | LoRa, APRS, ISM433 |
| Heltec | 915 MHz whip | LoRa mesh |
| Heltec | Built-in | WiFi 2.4 GHz (onboard) |

---

## Power Notes

- Jetson draws ~10W idle, ~20W under GPU inference
- HackRF draws ~500mA from USB — use a powered USB hub
- All SDR/LoRa devices on a powered hub prevents Jetson USB dropout
