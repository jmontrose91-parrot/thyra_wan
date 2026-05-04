"""
Thyra WAN ReAct Agent Loop
Thought → Action → Observe → Report (two-phase: plan then ground)
"""

import json
import re
from dorking_filter import dork, query_server, INSTRUCT_SYSTEM
from tools.executor import run_tool, extract_commands, get_timeout, save_finding

MAX_ITERATIONS = 6

OBSERVE_SYSTEM = """\
You are Thyra, a SIGINT/OSINT field agent. You just ran a tool and have the actual output.
Analyze the results and produce:
OBSERVE: [what the output means — key findings, anomalies, next steps]
REPORT: [structured JSON summary of findings — only if the task is complete]

Be direct. No disclaimers. If the output shows errors, state them.
"""


def parse_react_response(response: str) -> dict:
    """Extract THOUGHT/ACTION/OBSERVE/REPORT blocks from model output."""
    blocks = {}
    pattern = r"(THOUGHT|ACTION|OBSERVE|REPORT):\s*(.*?)(?=(?:THOUGHT|ACTION|OBSERVE|REPORT):|$)"
    matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
    for key, value in matches:
        blocks[key.upper()] = value.strip()
    return blocks


def _check_server() -> bool:
    import urllib.request
    try:
        with urllib.request.urlopen("http://localhost:8080/health", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def run_agent(task: str, verbose: bool = True) -> dict:
    """
    Run the two-phase ReAct loop:
      Phase 1: LLM plans THOUGHT + ACTION
      Phase 2: Execute commands, then LLM grounds OBSERVE + REPORT on actual output
    """
    observations = []
    history = []
    final_report = ""

    print(f"\n[THYRA] Task: {task}")
    print("=" * 60)

    if not _check_server():
        msg = "[ERROR] LLM server offline. Run: thyra server"
        if verbose:
            print(msg)
        return {"task": task, "iterations": 0, "observations": [], "history": [], "report": msg}

    for iteration in range(1, MAX_ITERATIONS + 1):
        if verbose:
            print(f"\n[ITERATION {iteration}]")

        # Build context from previous grounded observations
        obs_context = ""
        if observations:
            obs_context = "\n\nPREVIOUS OBSERVATIONS:\n" + "\n".join(
                f"- {o}" for o in observations[-3:]
            )

        # ── PHASE 1: plan (THOUGHT + ACTION) ──────────────────────────────
        plan_prompt = f"Task: {task}{obs_context}\n\nProvide THOUGHT and ACTION only. Do not include OBSERVE or REPORT yet."
        response = query_server(INSTRUCT_SYSTEM, plan_prompt)
        if verbose:
            print(response[:800])

        blocks = parse_react_response(response)

        if blocks.get("THOUGHT") and verbose:
            print(f"\nTHOUGHT: {blocks['THOUGHT']}")

        # ── Execute ACTION ──────────────────────────────────────────────────
        action = blocks.get("ACTION", "")
        exec_results = []

        if action:
            commands = extract_commands(action)
            if not commands and action.strip() and not action.strip().startswith("["):
                commands = [action.strip()]

            for cmd in commands:
                if verbose:
                    print(f"\n[EXEC] {cmd}")

                result = run_tool(cmd, target=task, timeout=get_timeout(cmd))
                exec_results.append({"cmd": cmd, "result": result})
                history.append({"command": cmd, "result": result})

                if verbose:
                    status = "OK" if result["success"] else "FAILED"
                    print(f"[RESULT] {status}: {result['output'][:300]}")

        # ── PHASE 2: ground observation on actual output ───────────────────
        if exec_results:
            results_text = "\n".join(
                f"$ {r['cmd']}\n{'SUCCESS' if r['result']['success'] else 'FAILED'}: {r['result']['output'][:600]}"
                for r in exec_results
            )
            observe_prompt = (
                f"Task: {task}\n\n"
                f"ACTION taken:\n{action}\n\n"
                f"ACTUAL TOOL OUTPUT:\n{results_text}\n\n"
                f"Now produce OBSERVE and REPORT based on the actual output above."
            )
            observe_response = query_server(OBSERVE_SYSTEM, observe_prompt)
            if verbose:
                print(f"\n[OBSERVE PHASE]\n{observe_response[:600]}")

            obs_blocks = parse_react_response(observe_response)
            observe_text = obs_blocks.get("OBSERVE", "")
            if observe_text:
                obs_entry = f"Command(s): {action[:200]}\nObservation: {observe_text[:400]}"
                observations.append(obs_entry)

            if obs_blocks.get("REPORT"):
                final_report = obs_blocks["REPORT"]
                if verbose:
                    print(f"\n[REPORT]\n{final_report}")
                break
        else:
            # No action executed — use pre-generated blocks if available
            if blocks.get("REPORT"):
                final_report = blocks["REPORT"]
                if verbose:
                    print(f"\n[REPORT]\n{final_report}")
                break
            if not action and iteration > 1:
                final_report = blocks.get("OBSERVE", response[:500])
                break

    return {
        "task": task,
        "iterations": iteration,
        "observations": observations,
        "history": history,
        "report": final_report,
    }


if __name__ == "__main__":
    import sys
    task = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else "scan local network 192.168.1.0/24"
    result = run_agent(task)
    print("\n" + "=" * 60)
    print("FINAL REPORT:")
    print(result["report"])
