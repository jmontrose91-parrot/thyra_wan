# Thyra Shopping List

Hardware needed to complete the build. Listed by priority.

---

## Priority 1 — WiFi Operations (needed for all WiFi commands)

### Alfa AWUS036ACH — ~$40
Dual-band monitor-mode WiFi adapter, 2.4 + 5 GHz. Required for `scan wifi`, `capture handshake`, `wifi clients`.
- Driver: rtl88xxau (built into JetPack, plug-and-play)
- [Search "AWUS036ACH" on Amazon]

---

## Priority 2 — SDR Antennas

### ANT500 Wideband SMA — ~$20
Telescoping wideband antenna, 75 MHz – 1 GHz. Attaches to HackRF SMA port for general sweeps.

### 2.4 GHz SMA Stubby — ~$8
Short stub antenna tuned for 2.4 GHz. Use on HackRF for WiFi/BT/Zigbee band scanning.

---

## Priority 3 — USB Power

### Powered USB Hub (4-port) — ~$15
Required once HackRF + RTL-SDR + Heltec + ESP32 are all plugged in simultaneously.
HackRF draws ~500mA — without a hub, the Jetson's USB ports will brown out under load.
- Any name-brand 4-port hub with its own power brick works.

---

## Priority 4 — Case Cabling

### SMA Bulkhead Connectors — ~$10 (pack of 4–6)
Panel-mount SMA female-to-female. Mount through the Pelican case wall so antennas connect from outside.
- Get enough for: HackRF, RTL-SDR, Heltec LoRa, and one spare.

---

## Summary

| Item | ~Cost | Blocks |
|---|---|---|
| Alfa AWUS036ACH | $40 | WiFi scanning, handshake capture |
| ANT500 wideband SMA | $20 | HackRF broadband sweeps |
| 2.4 GHz SMA stubby | $8 | HackRF WiFi/BT band |
| Powered USB hub (4-port) | $15 | Multi-device USB stability |
| SMA bulkhead connectors | $10 | Pelican case antenna passthrough |
| **Total** | **~$93** | |

---

## Already Have

- HackRF One
- ESP32-S3 PinPulse Shield (needs Marauder firmware)
- Heltec WiFi LoRa 32 V4 (needs Meshtastic firmware)
- NullLab RF-Nano (MouseJack)
- Base Duo LoRa repeater
- 915 MHz antennas x4
- 2.8" TFT 240x320 SPI display (not yet wired)
- Pelican case (hardware not yet mounted)
