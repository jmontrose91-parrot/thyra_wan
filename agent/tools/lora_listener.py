"""
Thyra LoRa/Meshtastic Listener
Receives messages and node info from Heltec LoRa 32 V4 running Meshtastic.
Device identified by USB tag: ID_MODEL contains 'heltec'
Usage: python3 lora_listener.py [--timeout 60]
"""

import json
import time
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import MESHTASTIC_BAUD
from tools.device_finder import find_heltec
from tools.executor import save_finding


def listen_meshtastic(port: str | None = None, timeout: int = 60) -> list[dict]:
    """
    Connect to Meshtastic device and collect packets for `timeout` seconds.
    Returns list of message dicts.
    """
    try:
        import meshtastic
        import meshtastic.serial_interface
    except ImportError:
        return [{"error": "meshtastic package not installed. Run: pip3 install meshtastic"}]

    port = port or find_heltec()
    if not port:
        return [{"error": "Heltec LoRa 32 V4 not found (ID_MODEL contains 'heltec')"}]

    messages = []
    start = time.time()

    def on_receive(packet, interface):
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        msg = {
            "timestamp": ts,
            "from": packet.get("fromId", "unknown"),
            "to":   packet.get("toId", "broadcast"),
            "type": packet.get("decoded", {}).get("portnum", "UNKNOWN"),
        }
        decoded = packet.get("decoded", {})
        if "text" in decoded:
            msg["text"] = decoded["text"]
        if "position" in decoded:
            pos = decoded["position"]
            msg["lat"]  = pos.get("latitudeI", 0) / 1e7
            msg["lon"]  = pos.get("longitudeI", 0) / 1e7
            msg["alt"]  = pos.get("altitude", 0)
        if "telemetry" in decoded:
            msg["telemetry"] = decoded["telemetry"]
        messages.append(msg)
        print(f"  [{ts}] from={msg['from']} type={msg['type']}"
              + (f" text={msg['text']!r}" if "text" in msg else "")
              + (f" pos=({msg.get('lat'):.4f},{msg.get('lon'):.4f})" if "lat" in msg else ""))

    try:
        iface = meshtastic.serial_interface.SerialInterface(devPath=port)
        print(f"[LoRa] Connected to {port} (heltec_wifi_lora_32_v4). Listening for {timeout}s...")

        # Register callback
        from pubsub import pub
        pub.subscribe(on_receive, "meshtastic.receive")

        # Wait for packets
        while time.time() - start < timeout:
            time.sleep(0.5)

        iface.close()
    except Exception as e:
        messages.append({"error": str(e), "port": port})
        print(f"[LoRa] Error: {e}")
        print(f"[LoRa] Check: is Heltec LoRa 32 V4 connected? (ID_MODEL=heltec_wifi_lora_32_v4)")

    return messages


def listen_serial_raw(port: str | None = None, baud: int = MESHTASTIC_BAUD,
                      timeout: int = 60) -> list[str]:
    """
    Raw serial listener — fallback if meshtastic package unavailable.
    Captures line-by-line output (works with Marauder, custom sketches, etc.)
    """
    try:
        import serial
    except ImportError:
        return ["pyserial not installed. Run: pip3 install pyserial"]

    port = port or find_heltec()
    if not port:
        return ["[ERROR] Heltec LoRa 32 V4 not found (ID_MODEL contains 'heltec')"]
    lines = []
    start = time.time()
    try:
        with serial.Serial(port, baud, timeout=1) as ser:
            print(f"[Serial] Listening on {port} (heltec_wifi_lora_32_v4) @ {baud} baud for {timeout}s...")
            while time.time() - start < timeout:
                line = ser.readline().decode(errors="ignore").strip()
                if line:
                    lines.append(line)
                    print(f"  {line}")
    except Exception as e:
        lines.append(f"[ERROR] {e}")
        print(f"[Serial] Error: {e}")
    return lines


def main():
    parser = argparse.ArgumentParser(description="Thyra LoRa/Meshtastic listener")
    parser.add_argument("--port",    default=None, help="Serial port (auto-detected if omitted)")
    parser.add_argument("--timeout", type=int, default=60)
    parser.add_argument("--raw",     action="store_true", help="Use raw serial instead of Meshtastic API")
    parser.add_argument("--baud",    type=int, default=MESHTASTIC_BAUD)
    args = parser.parse_args()

    if args.raw:
        results = listen_serial_raw(args.port, args.baud, args.timeout)
        output = "\n".join(results)
    else:
        packets = listen_meshtastic(args.port, args.timeout)
        output = json.dumps(packets, indent=2)

    save_finding("lora_listener", f"listen {args.port} {args.timeout}s",
                 args.port, output, f"{len(output.splitlines())} packets/lines")

    print(f"\n[LoRa] Captured {len(output.splitlines())} lines. Saved to findings DB.")
    print(output[:1000] if len(output) > 1000 else output)


if __name__ == "__main__":
    main()
