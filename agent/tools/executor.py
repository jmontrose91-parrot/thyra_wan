"""
Thyra WAN Tool Executor
Runs CLI security tools and captures structured output.
"""

import subprocess
import json
import os
import sqlite3
import time
from pathlib import Path

DB_PATH = Path.home() / "findings.db"
OUTPUT_DIR = Path("/tmp/thyra_output")
OUTPUT_DIR.mkdir(exist_ok=True)


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS findings (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT    NOT NULL,
            target    TEXT,
            tool      TEXT    NOT NULL,
            command   TEXT    NOT NULL,
            result    TEXT,
            summary   TEXT
        )
    """)
    conn.commit()
    return conn


def save_finding(tool: str, command: str, target: str, result: str, summary: str = ""):
    conn = init_db()
    conn.execute(
        "INSERT INTO findings (timestamp, target, tool, command, result, summary) VALUES (?,?,?,?,?,?)",
        (time.strftime("%Y-%m-%dT%H:%M:%S"), target, tool, command, result[:4096], summary),
    )
    conn.commit()
    conn.close()


def run_tool(command: str, target: str = "", timeout: int = 120) -> dict:
    """
    Execute a CLI tool command. Returns structured result.
    """
    tool_name = command.split()[0]
    output_file = OUTPUT_DIR / f"{tool_name}_{int(time.time())}.out"

    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        combined = stdout or stderr

        # Try to parse as JSON if tool outputs JSON
        parsed = None
        try:
            parsed = json.loads(stdout)
        except (json.JSONDecodeError, ValueError):
            pass

        output_file.write_text(combined)
        save_finding(tool_name, command, target, combined)

        return {
            "success": result.returncode == 0,
            "returncode": result.returncode,
            "output": combined,
            "parsed": parsed,
            "output_file": str(output_file),
            "tool": tool_name,
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "returncode": -1,
            "output": f"[TIMEOUT] Command exceeded {timeout}s limit",
            "parsed": None,
            "output_file": None,
            "tool": tool_name,
        }
    except Exception as e:
        return {
            "success": False,
            "returncode": -1,
            "output": f"[ERROR] {e}",
            "parsed": None,
            "output_file": None,
            "tool": tool_name,
        }


def extract_commands(llm_response: str) -> list[str]:
    """
    Parse LLM response and extract executable CLI commands.
    Handles numbered lists, code blocks, and bare commands.
    """
    commands = []
    lines = llm_response.split("\n")
    in_code_block = False

    for line in lines:
        line = line.strip()

        if line.startswith("```"):
            in_code_block = not in_code_block
            continue

        if in_code_block:
            if line and not line.startswith("#"):
                commands.append(line)
            continue

        # Numbered list: "1. nmap ..."
        if line and line[0].isdigit() and ". " in line:
            cmd = line.split(". ", 1)[1].strip()
            if cmd and not cmd.startswith("#"):
                commands.append(cmd)
            continue

        # Backtick inline code
        if "`" in line:
            import re
            matches = re.findall(r"`([^`]+)`", line)
            for m in matches:
                if any(m.startswith(t) for t in ("nmap", "masscan", "tshark", "aircrack",
                                                   "rtl_", "dump1090", "theHarvester",
                                                   "dnsrecon", "gobuster", "ffuf", "nikto",
                                                   "sqlmap", "hackrf", "hping", "wget", "curl")):
                    commands.append(m)

    return commands


TOOL_TIMEOUTS = {
    "nmap": 300,
    "masscan": 60,
    "tshark": 30,
    "airodump-ng": 60,
    "aireplay-ng": 30,
    "rtl_433": 60,
    "dump1090": 30,
    "theHarvester": 120,
    "dnsrecon": 60,
    "gobuster": 120,
    "ffuf": 120,
    "nikto": 180,
    "hackrf_sweep": 60,
}


def get_timeout(command: str) -> int:
    tool = command.split()[0]
    return TOOL_TIMEOUTS.get(tool, 120)
