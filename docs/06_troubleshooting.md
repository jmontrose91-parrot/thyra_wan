# Troubleshooting

## Quick Diagnostics

```bash
# Full system status (run this first)
thyra status

# Self-test (61 checks)
thyra smoke
```

---

## LLM Server Issues

### Server not responding
```bash
sudo systemctl status thyra-llama
sudo systemctl restart thyra-llama
thyra server    # waits up to 120s for /health
```

### Server keeps crashing
```bash
# Check journal for error
sudo journalctl -u thyra-llama --no-pager -n 30

# Common causes:
# 1. Model file incomplete — check size
ls -lh ~/models/
# Qwen3 should be ~5.0 GB, Coder ~4.68 GB

# 2. Out of VRAM — check usage
cat /proc/driver/nvidia/params 2>/dev/null | grep -i mem

# 3. Wrong CUDA path — verify
/home/thyra/llama.cpp/build/bin/llama-server --version
```

### Model not loading (blank inference output)
Qwen3 uses chain-of-thought by default. The agent appends `/no_think` to disable it. If you're calling the API directly, add `/no_think` to your user message or set `thinking: false` in the request.

---

## SSH Issues

### `Permission denied (publickey)`
Your key isn't authorized on the Jetson.
```bash
# Use password auth once to add your key:
ssh-copy-id thyra@192.168.55.1
# or:
ssh-copy-id thyra@orin-nano
```

### Can't reach 192.168.55.1
USB-C gadget interface isn't up.
```bash
# On Parrot — check the interface:
ip addr show enxa6b42d583d18
# Should have 192.168.55.x address

# If missing, replug USB-C cable
# The Jetson creates the gadget interface at boot
```

### SSH times out (Tailscale)
```bash
# Check Tailscale on Jetson:
ssh thyra@192.168.55.1 "tailscale status"

# If not connected:
ssh thyra@192.168.55.1 "sudo tailscale up"
# Then visit the auth URL it prints
```

---

## VNC Issues

### Can't connect to 5901
```bash
# Check if VNC is running:
ssh thyra "ss -tnlp | grep 5901"

# Restart VNC service:
ssh thyra "sudo systemctl restart vncserver@thyra"
```

### Black screen in VNC
Openbox crashed or didn't start.
```bash
ssh thyra "DISPLAY=:1 openbox-session &"
# or restart the VNC session:
ssh thyra "sudo systemctl restart vncserver@thyra"
```

### VNC too slow
- Over local network/USB-C: should be fast
- Over internet: normal VNC is uncompressed — try SSH tunnel for better performance
- Lower resolution: edit `/etc/systemd/system/vncserver@thyra.service`, change `1280x800` to `1024x600`

---

## WiFi / Alfa Adapter Issues

### No wlan0
```bash
# Check USB
lsusb | grep -i realtek
# Replug adapter if not shown

# Check driver
dmesg | grep -i rtl88
```

### airmon-ng fails
```bash
# Kill interfering processes first
sudo airmon-ng check kill
sudo airmon-ng start wlan0
```

---

## SDR / HackRF Issues

### `hackrf_info` fails
```bash
# Check USB
lsusb | grep -i hackrf
# Reset USB device
sudo usbreset $(lsusb | grep HackRF | awk '{print $2"/"$4}' | tr -d :)
```

### RTL-SDR device not found
```bash
lsusb | grep -E "0bda:2838|Realtek"
# Add udev rules if permission denied:
sudo usermod -aG plugdev thyra
```

### LoRa no data from /dev/ttyUSB0
```bash
# Check device exists
ls -la /dev/ttyUSB*

# Check Meshtastic firmware is flashed
minicom -D /dev/ttyUSB0 -b 115200
# Should see JSON packets if firmware is running
```

---

## Agent / Python Issues

### `thyra` command not found
```bash
export PATH="$HOME/.local/bin:$PATH"
# Add to ~/.bashrc permanently:
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```

### Import errors in smoke test
```bash
# Reinstall Python deps
pip3 install requests rich openai sqlite-utils meshtastic kismet-rest
pip3 install python_hackrf  # needs: sudo apt install libusb-1.0-0-dev
```

### `pyrtlsdr` import error (librtlsdr symbol)
Known issue — system librtlsdr.so is older than pyrtlsdr expects. This is a WARN, not a FAIL. RTL-SDR still works via CLI tools (`rtl_433`, `rtl_power`). No action needed.

---

## Full Reset / Reinstall Agent

```bash
cd ~/agent
bash setup.sh   # re-runs full install
thyra smoke     # verify
```
