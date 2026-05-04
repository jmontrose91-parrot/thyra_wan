"""
Thyra HackRF SDR Tool
Uses python_hackrf (pip install python_hackrf) for sweep and receive operations.
Falls back to hackrf_sweep CLI if python_hackrf unavailable.
Usage: python3 hackrf_sdr.py --mode sweep --start 100 --end 500
"""
import json
import subprocess
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import HACKRF_GAIN_LNA, HACKRF_GAIN_VGA, HACKRF_SAMPLE_RATE
from tools.executor import save_finding


def sweep_cli(start_mhz: int, end_mhz: int, lna: int = HACKRF_GAIN_LNA,
              vga: int = HACKRF_GAIN_VGA, bin_width: int = 100000,
              duration: int = 5) -> list[dict]:
    """
    Run hackrf_sweep CLI and return list of {freq_mhz, power_db}.
    Terminates after `duration` seconds.
    """
    cmd = [
        "hackrf_sweep",
        f"-f", f"{start_mhz}:{end_mhz}",
        f"-l", str(lna),
        f"-g", str(vga),
        f"-w", str(bin_width),
    ]
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                text=True)
        lines = []
        deadline = time.time() + duration
        while time.time() < deadline:
            line = proc.stdout.readline()
            if line:
                lines.append(line.strip())
        proc.terminate()
    except FileNotFoundError:
        return [{"error": "hackrf_sweep not found — install hackrf package"}]
    except Exception as e:
        return [{"error": str(e)}]

    readings = []
    for line in lines:
        parts = line.split(",")
        if len(parts) < 6:
            continue
        try:
            freq_low  = float(parts[2])
            freq_high = float(parts[3])
            step      = float(parts[4])
            powers    = [float(x) for x in parts[6:] if x.strip()]
            for i, pwr in enumerate(powers):
                freq_hz = freq_low + i * step
                readings.append({
                    "freq_mhz": round(freq_hz / 1e6, 3),
                    "power_db": round(pwr, 1),
                })
        except (ValueError, IndexError):
            continue
    return readings


def sweep_python(start_mhz: int, end_mhz: int, lna: int = HACKRF_GAIN_LNA,
                 vga: int = HACKRF_GAIN_VGA, duration: int = 5) -> list[dict]:
    """
    Sweep using python_hackrf library (more pythonic, same underlying libhackrf).
    """
    try:
        from python_hackrf import pyhackrf
    except ImportError:
        return [{"error": "python_hackrf not installed — pip3 install python_hackrf"}]

    readings = []
    collected = []

    try:
        hackrf = pyhackrf.PyHackrfDevice()
        hackrf.set_lna_gain(lna)
        hackrf.set_vga_gain(vga)
        hackrf.set_sample_rate(int(HACKRF_SAMPLE_RATE))
        hackrf.set_freq(int(start_mhz * 1e6))
        hackrf.start_rx()

        deadline = time.time() + duration
        while time.time() < deadline:
            buf = hackrf.receive(16384)
            if buf:
                collected.append(buf)
            time.sleep(0.01)

        hackrf.stop_rx()
        hackrf.close()

        # Simple power estimate: mean square of I/Q samples
        import struct, math
        for buf in collected:
            samples = struct.unpack(f"{len(buf)//2}h", buf[:len(buf)//2*2]) if len(buf) >= 2 else []
            if samples:
                mean_pwr = 10 * math.log10(sum(s**2 for s in samples) / len(samples) + 1e-12)
                readings.append({"freq_mhz": start_mhz, "power_db": round(mean_pwr, 1)})

    except Exception as e:
        return [{"error": str(e)}]

    return readings if readings else [{"error": "no data received"}]


def top_signals(readings: list[dict], n: int = 20, threshold: float = -60.0) -> list[dict]:
    above = [r for r in readings if r.get("power_db", -999) > threshold]
    return sorted(above, key=lambda x: x["power_db"], reverse=True)[:n]


def main():
    parser = argparse.ArgumentParser(description="Thyra HackRF SDR tool")
    parser.add_argument("--mode",      choices=["sweep", "sweep-py"], default="sweep")
    parser.add_argument("--start",     type=int, default=100,   help="Start MHz")
    parser.add_argument("--end",       type=int, default=500,   help="End MHz")
    parser.add_argument("--lna",       type=int, default=HACKRF_GAIN_LNA)
    parser.add_argument("--vga",       type=int, default=HACKRF_GAIN_VGA)
    parser.add_argument("--time",      type=int, default=5,     help="Sweep seconds")
    parser.add_argument("--threshold", type=float, default=-60.0)
    parser.add_argument("--top",       type=int, default=20)
    args = parser.parse_args()

    print(f"[HackRF] {args.mode} {args.start}–{args.end} MHz for {args.time}s...")

    if args.mode == "sweep-py":
        readings = sweep_python(args.start, args.end, args.lna, args.vga, args.time)
    else:
        readings = sweep_cli(args.start, args.end, args.lna, args.vga, duration=args.time)

    if readings and "error" in readings[0]:
        print(f"[ERROR] {readings[0]['error']}")
        sys.exit(1)

    signals = top_signals(readings, args.top, args.threshold)
    result = {
        "total_readings": len(readings),
        "top_signals": signals,
        "range_mhz": f"{args.start}-{args.end}",
    }
    out = json.dumps(result, indent=2)
    print(out)

    save_finding("hackrf_sdr", f"hackrf sweep {args.start}:{args.end}MHz",
                 f"{args.start}:{args.end}MHz", out,
                 f"{len(readings)} readings, {len(signals)} above {args.threshold} dBm")


if __name__ == "__main__":
    main()
