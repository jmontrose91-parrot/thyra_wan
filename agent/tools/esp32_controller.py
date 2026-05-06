"""
ThyraESP32 serial controller.
Communicates with the Lonely Binary PinPulse Shield running ThyraESP32 firmware.
Device: /dev/ttyACM0 (when plugged into Jetson, not conflicting with Jetson gadget UART)
"""
import serial
import json
import time
import os

ESP32_PORT = os.environ.get("THYRA_ESP32_PORT", "/dev/ttyACM0")
BAUD = 115200
DEFAULT_TIMEOUT = 10


def _find_port():
    import glob
    import subprocess
    candidates = sorted(glob.glob("/dev/ttyACM*"))
    # First pass: prefer the PinPulse Shield (ESP32S3_DEV), not Heltec
    for port in candidates:
        try:
            result = subprocess.run(
                ["udevadm", "info", port], capture_output=True, text=True
            )
            if "ESP32S3_DEV" in result.stdout:
                return port
        except Exception:
            pass
    # Fallback: any Espressif device
    for port in candidates:
        try:
            result = subprocess.run(
                ["udevadm", "info", port], capture_output=True, text=True
            )
            if "303a" in result.stdout or "Espressif" in result.stdout:
                return port
        except Exception:
            pass
    return ESP32_PORT


def send_command(cmd: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    port = _find_port()
    try:
        with serial.Serial(port, BAUD, timeout=timeout) as s:
            time.sleep(0.3)
            s.reset_input_buffer()
            s.write((cmd.strip() + "\n").encode())
            lines = []
            deadline = time.time() + timeout
            while time.time() < deadline:
                line = s.readline().decode(errors="ignore").strip()
                if line:
                    lines.append(line)
                    # Stop after we have a complete JSON response
                    if lines and (lines[-1].startswith("{") or lines[-1].endswith("]")):
                        break
            raw = "\n".join(lines)
            try:
                return {"success": True, "data": json.loads(raw), "raw": raw}
            except json.JSONDecodeError:
                return {"success": True, "raw": raw}
    except serial.SerialException as e:
        return {"success": False, "error": str(e), "port": port}


def wifi_scan() -> dict:
    return send_command("scan", timeout=15)


def deauth(bssid: str, channel: int, count: int = 20) -> dict:
    return send_command(f"deauth {bssid} {channel} {count}", timeout=10)


def ble_scan(seconds: int = 5) -> dict:
    return send_command(f"ble_scan {seconds}", timeout=seconds + 5)


def set_channel(channel: int) -> dict:
    return send_command(f"channel {channel}", timeout=5)


def status() -> dict:
    return send_command("status", timeout=5)


if __name__ == "__main__":
    print("ESP32 status:", json.dumps(status(), indent=2))
