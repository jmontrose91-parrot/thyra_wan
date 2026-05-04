"""
Thyra Kismet REST Client
Polls the Kismet REST API for WiFi devices, alerts, and packets.
Requires: kismet running headless, kismet-rest pip package.
Usage: python3 kismet_client.py [--host localhost] [--port 2501] [--time 60]
"""
import json
import time
import sys
import subprocess
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from tools.executor import save_finding


KISMET_DEFAULT_USER = "kismet"
KISMET_DEFAULT_PASS = "kismet"


def start_kismet_server(interface: str = "wlan0") -> subprocess.Popen:
    """Start kismet_server headlessly. Returns the process."""
    cmd = f"kismet -c {interface} --no-ncurses --daemonize --log-type pcapng"
    proc = subprocess.Popen(cmd.split(), stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)
    time.sleep(5)  # wait for server startup
    return proc


def get_devices(host: str = "localhost", port: int = 2501,
                user: str = KISMET_DEFAULT_USER,
                password: str = KISMET_DEFAULT_PASS) -> list[dict]:
    """
    Fetch all seen WiFi devices from Kismet REST API.
    Returns list of device dicts with SSID, BSSID, channel, signal.
    """
    try:
        import kismet_rest
    except ImportError:
        return [{"error": "kismet-rest not installed. Run: pip3 install kismet-rest"}]

    try:
        ks = kismet_rest.KismetConnector(
            host=f"http://{host}:{port}",
            username=user,
            password=password,
        )
        devices = []
        for dev in ks.device_list():
            d = {
                "mac":      dev.get("kismet.device.base.macaddr", ""),
                "type":     dev.get("kismet.device.base.type", ""),
                "channel":  dev.get("kismet.device.base.channel", ""),
                "signal":   dev.get("kismet.device.base.signal", {}).get("kismet.common.signal.last_signal", 0),
                "packets":  dev.get("kismet.device.base.packets.total", 0),
                "first":    dev.get("kismet.device.base.first_time", 0),
                "last":     dev.get("kismet.device.base.last_time", 0),
            }
            # SSID from advertised SSID list
            ssid_list = dev.get("dot11.device", {}).get("dot11.device.advertised_ssid_map", {})
            if ssid_list:
                first_ssid = next(iter(ssid_list.values()), {})
                d["ssid"] = first_ssid.get("dot11.advertisedssid.ssid", "")
                d["encryption"] = first_ssid.get("dot11.advertisedssid.crypt_string", "")
            devices.append(d)
        return devices
    except Exception as e:
        return [{"error": str(e)}]


def main():
    parser = argparse.ArgumentParser(description="Thyra Kismet client")
    parser.add_argument("--host",      default="localhost")
    parser.add_argument("--port",      type=int, default=2501)
    parser.add_argument("--interface", default="wlan0",
                        help="WiFi interface to monitor (if starting kismet)")
    parser.add_argument("--time",      type=int, default=60)
    parser.add_argument("--start",     action="store_true",
                        help="Start kismet_server before querying")
    args = parser.parse_args()

    proc = None
    if args.start:
        print(f"[Kismet] Starting server on {args.interface}...")
        proc = start_kismet_server(args.interface)

    print(f"[Kismet] Waiting {args.time}s, then querying {args.host}:{args.port}...")
    time.sleep(args.time)

    devices = get_devices(args.host, args.port)
    if devices and "error" in devices[0]:
        print(f"[ERROR] {devices[0]['error']}")
        if proc:
            proc.terminate()
        sys.exit(1)

    # Sort by signal strength
    devices.sort(key=lambda d: d.get("signal", -999), reverse=True)
    out = json.dumps(devices, indent=2)
    print(out)

    save_finding("kismet", f"kismet {args.interface} {args.time}s",
                 args.interface, out,
                 f"{len(devices)} devices seen")
    print(f"\n[Kismet] {len(devices)} devices found. Saved to findings DB.")

    if proc:
        proc.terminate()


if __name__ == "__main__":
    main()
