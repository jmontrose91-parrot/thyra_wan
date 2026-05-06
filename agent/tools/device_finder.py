"""
Thyra WAN — USB Serial Device Finder
Identifies serial ports by USB device identity tag, not port number.
"""
import glob
import subprocess
import os

_CACHE: dict[str, str] = {}


def _udev_info(port: str) -> str:
    if port not in _CACHE:
        try:
            r = subprocess.run(["udevadm", "info", port], capture_output=True, text=True)
            _CACHE[port] = r.stdout
        except Exception:
            _CACHE[port] = ""
    return _CACHE[port]


def find_port(tag: str, fallback: str | None = None) -> str | None:
    """
    Return the first /dev/ttyACM* or /dev/ttyUSB* whose udevadm ID_MODEL
    contains `tag` (case-insensitive). Returns `fallback` if not found.
    """
    tag_lower = tag.lower()
    candidates = sorted(glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*"))
    for port in candidates:
        for line in _udev_info(port).splitlines():
            if line.startswith("E: ID_MODEL=") and tag_lower in line.lower():
                return port
    return fallback


def find_pinpulse() -> str | None:
    """PinPulse Shield (ThyraESP32 firmware) — ID_MODEL: ESP32S3_DEV"""
    return find_port("ESP32S3_DEV", os.environ.get("THYRA_ESP32_PORT"))


def find_heltec() -> str | None:
    """Heltec LoRa 32 V4 (Meshtastic) — ID_MODEL: heltec_wifi_lora_32_v4..."""
    return find_port("heltec", os.environ.get("THYRA_LORA_PORT"))


def find_nrf24() -> str | None:
    """RF-Nano v3 (nRF24L01+) — ID_VENDOR=1a86, ID_MODEL=USB_Serial (QinHeng CH340)"""
    import subprocess
    import glob
    for port in sorted(glob.glob("/dev/ttyUSB*")):
        try:
            r = subprocess.run(["udevadm", "info", port], capture_output=True, text=True)
            if "1a86" in r.stdout and "USB_Serial" in r.stdout:
                return port
        except Exception:
            pass
    return os.environ.get("THYRA_NRF24_LOCAL_PORT")


def list_devices() -> dict[str, str | None]:
    """Return a snapshot of all known Thyra serial devices and their current ports."""
    return {
        "pinpulse": find_pinpulse(),
        "heltec_lora": find_heltec(),
        "nrf24_rfnano": find_nrf24(),
    }
