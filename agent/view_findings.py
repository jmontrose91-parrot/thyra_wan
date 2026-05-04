"""
Thyra Findings Viewer
Usage: python3 view_findings.py [--target TARGET] [--tool TOOL] [--last N]
"""
import sqlite3
import sys
import argparse
from pathlib import Path
from datetime import datetime

DB_PATH = Path.home() / "findings.db"


def format_table(rows, headers):
    widths = [len(h) for h in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))

    sep = "+" + "+".join("-" * (w + 2) for w in widths) + "+"
    header_row = "|" + "|".join(f" {h:<{widths[i]}} " for i, h in enumerate(headers)) + "|"

    lines = [sep, header_row, sep]
    for row in rows:
        line = "|" + "|".join(f" {str(cell):<{widths[i]}} " for i, cell in enumerate(row)) + "|"
        lines.append(line)
    lines.append(sep)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="View Thyra findings database")
    parser.add_argument("--target", "-t", help="Filter by target")
    parser.add_argument("--tool", help="Filter by tool")
    parser.add_argument("--last", "-n", type=int, default=20, help="Show last N findings (default 20)")
    parser.add_argument("--detail", "-d", type=int, help="Show full detail for finding ID")
    parser.add_argument("--clear", action="store_true", help="Clear all findings (with confirmation)")
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"No findings database at {DB_PATH}")
        print("Run some scans first.")
        return

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    if args.clear:
        confirm = input("Clear ALL findings? (yes/no): ").strip()
        if confirm.lower() == "yes":
            conn.execute("DELETE FROM findings")
            conn.commit()
            print("Findings cleared.")
        return

    if args.detail:
        row = conn.execute("SELECT * FROM findings WHERE id = ?", (args.detail,)).fetchone()
        if not row:
            print(f"No finding with ID {args.detail}")
            return
        print(f"\n{'='*60}")
        print(f"ID:        {row['id']}")
        print(f"Time:      {row['timestamp']}")
        print(f"Target:    {row['target']}")
        print(f"Tool:      {row['tool']}")
        print(f"Command:   {row['command']}")
        if row['summary']:
            print(f"Summary:   {row['summary']}")
        print(f"\nFull Output:\n{'-'*60}")
        print(row['result'] or "(empty)")
        print("="*60)
        return

    # Build query
    where_clauses = []
    params = []
    if args.target:
        where_clauses.append("target LIKE ?")
        params.append(f"%{args.target}%")
    if args.tool:
        where_clauses.append("tool LIKE ?")
        params.append(f"%{args.tool}%")

    where = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
    query = f"SELECT id, timestamp, target, tool, command, result FROM findings {where} ORDER BY id DESC LIMIT {args.last}"

    rows = conn.execute(query, params).fetchall()
    total = conn.execute(f"SELECT count(*) FROM findings {where}", params).fetchone()[0]

    if not rows:
        print("No findings match the filter.")
        return

    table_rows = []
    for r in rows:
        cmd_short = r['command'][:40] + "..." if len(r['command']) > 40 else r['command']
        result_short = (r['result'] or "")[:50].replace("\n", " ") + ("..." if len(r['result'] or "") > 50 else "")
        table_rows.append([r['id'], r['timestamp'][:16], r['target'][:20], r['tool'], cmd_short, result_short])

    print(f"\nFindings ({min(args.last, total)}/{total} shown):")
    print(format_table(table_rows, ["ID", "Timestamp", "Target", "Tool", "Command", "Result Preview"]))
    print(f"\nUse --detail ID for full output. Use --last N to show more.")


if __name__ == "__main__":
    main()
