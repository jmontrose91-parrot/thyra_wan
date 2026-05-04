"""
rtl_power CSV → JSON converter
Runs rtl_power and converts its CSV output to structured JSON.
Usage: python3 rtl_power_json.py --freq 88M:108M:100k --time 10
"""
import subprocess
import csv
import json
import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import RTL_GAIN
from tools.executor import save_finding


def rtl_power_to_json(freq_range: str = "88M:108M:100k",
                      integration: int = 1,
                      duration: int = 30,
                      gain: int = RTL_GAIN,
                      output_file: str = "/tmp/rtl_power.csv") -> list[dict]:
    """
    Run rtl_power and return list of {freq_hz, power_db, timestamp} dicts.
    freq_range: "start:end:step"  e.g. "88M:108M:100k"
    """
    cmd = (f"rtl_power -f {freq_range} -g {gain} -i {integration} "
           f"-1 {output_file}")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True,
                                text=True, timeout=duration + 10)
    except subprocess.TimeoutExpired:
        return [{"error": "rtl_power timed out"}]
    except FileNotFoundError:
        return [{"error": "rtl_power not found — install rtl-sdr package"}]

    readings = []
    try:
        with open(output_file) as f:
            for row in csv.reader(f):
                if len(row) < 7:
                    continue
                timestamp = row[0].strip() + " " + row[1].strip()
                freq_start = float(row[2])
                freq_end   = float(row[3])
                freq_step  = float(row[4])
                # row[6:] are the power readings in dB
                powers = [float(x) for x in row[6:] if x.strip()]
                for i, pwr in enumerate(powers):
                    freq_hz = freq_start + i * freq_step
                    readings.append({
                        "timestamp": timestamp,
                        "freq_hz":   freq_hz,
                        "freq_mhz":  round(freq_hz / 1e6, 3),
                        "power_db":  pwr,
                    })
    except (FileNotFoundError, ValueError, IndexError) as e:
        return [{"error": f"parse error: {e}"}]

    return readings


def top_signals(readings: list[dict], n: int = 10, threshold: float = -60.0) -> list[dict]:
    """Return top N strongest signals above threshold, sorted by power."""
    above = [r for r in readings if r.get("power_db", -999) > threshold]
    return sorted(above, key=lambda x: x["power_db"], reverse=True)[:n]


def main():
    parser = argparse.ArgumentParser(description="rtl_power JSON wrapper")
    parser.add_argument("--freq",  default="88M:108M:100k", help="start:end:step")
    parser.add_argument("--time",  type=int, default=30,    help="capture seconds")
    parser.add_argument("--gain",  type=int, default=RTL_GAIN)
    parser.add_argument("--top",   type=int, default=20,    help="show top N signals")
    parser.add_argument("--threshold", type=float, default=-70.0)
    args = parser.parse_args()

    print(f"[rtl_power] Scanning {args.freq} for {args.time}s...")
    readings = rtl_power_to_json(args.freq, duration=args.time, gain=args.gain)

    if readings and "error" in readings[0]:
        print(f"[ERROR] {readings[0]['error']}")
        sys.exit(1)

    top = top_signals(readings, args.top, args.threshold)
    result = {"total_readings": len(readings), "top_signals": top}
    out = json.dumps(result, indent=2)
    print(out)
    save_finding("rtl_power", f"rtl_power -f {args.freq}", args.freq,
                 out, f"{len(readings)} readings, {len(top)} above {args.threshold} dB")


if __name__ == "__main__":
    main()
