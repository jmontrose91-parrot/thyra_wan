"""
ThyraESP32 serial controller.
Communicates with the Lonely Binary PinPulse Shield running ThyraESP32 firmware.
Device identified by USB tag: ID_MODEL=ESP32S3_DEV
"""
import serial
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from device_finder import find_pinpulse

BAUD = 115200
DEFAULT_TIMEOUT = 10


def send_command(cmd: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    port = find_pinpulse()
    if not port:
        return {"success": False, "error": "PinPulse Shield not found (ID_MODEL=ESP32S3_DEV)"}
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
                    if lines and (lines[-1].startswith("{") or lines[-1].endswith("]")):
                        break
            raw = "\n".join(lines)
            try:
                return {"success": True, "data": json.loads(raw), "raw": raw, "port": port}
            except json.JSONDecodeError:
                return {"success": True, "raw": raw, "port": port}
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
