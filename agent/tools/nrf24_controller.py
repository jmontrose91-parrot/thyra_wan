"""
Thyra NRF24 controller.
Communicates with RF-Nano v3 (ATmega328P + nRF24L01+, CH340 USB-serial).
Connects via local /dev/ttyUSB* or TCP (ser2net bridge) when on Thyra.

Device identified by: ID_MODEL=USB_Serial AND ID_VENDOR=1a86 (QinHeng CH340)
TCP bridge: run on Parrot → ser2net -C '4000:raw:0:/dev/ttyUSB0:115200'
"""
import json
import time
import os
import socket

BAUD = 115200
DEFAULT_TIMEOUT = 15
TCP_HOST = os.environ.get("THYRA_NRF24_HOST", "100.78.108.17")  # Parrot Tailscale IP
TCP_PORT = int(os.environ.get("THYRA_NRF24_PORT", "4000"))


def _find_local_port() -> str | None:
    import glob
    import subprocess
    for port in sorted(glob.glob("/dev/ttyUSB*")):
        try:
            r = subprocess.run(["udevadm", "info", port], capture_output=True, text=True)
            if "1a86" in r.stdout and "USB_Serial" in r.stdout:
                return port
        except Exception:
            pass
    return None


class _SerialConn:
    def __init__(self, port: str):
        import serial
        self._s = serial.Serial()
        self._s.port = port
        self._s.baudrate = BAUD
        self._s.dtr = False  # suppress Arduino auto-reset on open
        self._s.timeout = 3
        self._s.open()
        time.sleep(2)
        self._s.reset_input_buffer()

    def write(self, data: bytes):
        self._s.write(data)

    def readline(self) -> bytes:
        return self._s.readline()

    def set_timeout(self, t: float):
        self._s.timeout = t

    def close(self):
        self._s.close()


class _TCPConn:
    def __init__(self, host: str, port: int):
        self._sock = socket.create_connection((host, port), timeout=5)
        self._sock.settimeout(3)
        self._buf = b""
        time.sleep(0.5)
        # drain startup
        try:
            self._sock.recv(512)
        except Exception:
            pass

    def write(self, data: bytes):
        self._sock.sendall(data)

    def readline(self) -> bytes:
        deadline = time.time() + self._timeout
        while b"\n" not in self._buf:
            try:
                chunk = self._sock.recv(256)
                if chunk:
                    self._buf += chunk
            except socket.timeout:
                break
            if time.time() > deadline:
                break
        if b"\n" in self._buf:
            line, self._buf = self._buf.split(b"\n", 1)
            return line + b"\n"
        return b""

    def set_timeout(self, t: float):
        self._timeout = t
        self._sock.settimeout(min(t, 5))

    _timeout = 3

    def close(self):
        self._sock.close()


def _connect() -> tuple[object, str]:
    port = _find_local_port()
    if port:
        return _SerialConn(port), f"serial:{port}"
    return _TCPConn(TCP_HOST, TCP_PORT), f"tcp:{TCP_HOST}:{TCP_PORT}"


def send_command(cmd: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    try:
        conn, via = _connect()
    except Exception as e:
        return {"success": False, "error": f"cannot connect to RF-Nano: {e}"}
    try:
        conn.set_timeout(timeout)
        conn.write((cmd.strip() + "\r\n").encode())
        lines = []
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = conn.readline().decode(errors="ignore").strip()
            if line:
                lines.append(line)
                if line.startswith("[") or (line.startswith("{") and
                        not line.startswith('{"scanning"') and
                        not line.startswith('{"sniffing"')):
                    break
        raw = "\n".join(lines)
        try:
            return {"success": True, "data": json.loads(raw), "raw": raw, "via": via}
        except json.JSONDecodeError:
            return {"success": True, "raw": raw, "via": via}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        try:
            conn.close()
        except Exception:
            pass


def status() -> dict:
    return send_command("status", timeout=5)


def channel_scan() -> dict:
    return send_command("scan", timeout=30)


def sniff(channel: int = 76, duration: int = 30) -> list[dict]:
    """Start sniff, collect packets for duration seconds, stop."""
    packets = []
    try:
        conn, via = _connect()
    except Exception as e:
        return [{"error": str(e)}]
    try:
        conn.set_timeout(2)
        conn.write(f"sniff {channel}\r\n".encode())
        deadline = time.time() + duration
        while time.time() < deadline:
            line = conn.readline().decode(errors="ignore").strip()
            if line and line.startswith('{"packet"'):
                try:
                    packets.append(json.loads(line))
                except Exception:
                    packets.append({"raw": line})
        conn.write(b"sniff_stop\r\n")
        time.sleep(0.5)
    finally:
        try:
            conn.close()
        except Exception:
            pass
    return packets


def set_channel(channel: int) -> dict:
    return send_command(f"set_channel {channel}", timeout=5)


def set_rate(kbps: int) -> dict:
    return send_command(f"set_rate {kbps}", timeout=5)


if __name__ == "__main__":
    print("RF-Nano status:", json.dumps(status(), indent=2))
