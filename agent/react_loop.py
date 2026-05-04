"""
Thyra WAN ReAct Agent Loop
Thought → Action → Observe → Report
"""

import json
import re
from dorking_filter import dork, query_server, INSTRUCT_SYSTEM
from tools.executor import run_tool, extract_commands, get_timeout, save_finding

MAX_ITERATIONS = 6


def parse_react_response(response: str) -> dict:
    """Extract THOUGHT/ACTION/OBSERVE/REPORT blocks from model output."""
    blocks = {}
    pattern = r"(THOUGHT|ACTION|OBSERVE|REPORT):\s*(.*?)(?=(?:THOUGHT|ACTION|OBSERVE|REPORT):|$)"
    matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)
    for key, value in matches:
        blocks[key.upper()] = value.strip()
    return blocks


def run_agent(task: str, verbose: bool = True) -> dict:
    """
    Run the ReAct loop for a given task.
    Returns final report dict.
    """
    observations = []
    history = []
    final_report = ""

    print(f"\n[THYRA] Task: {task}")
    print("=" * 60)

    for iteration in range(1, MAX_ITERATIONS + 1):
        if verbose:
            print(f"\n[ITERATION {iteration}]")

        # Build context from previous observations
        obs_context = ""
        if observations:
            obs_context = "\n\nPREVIOUS OBSERVATIONS:\n" + "\n".join(
                f"- {o}" for o in observations[-3:]  # last 3 observations
            )

        user_msg = f"Task: {task}{obs_context}"

        response = query_server(INSTRUCT_SYSTEM, user_msg)
        if verbose:
            print(response[:1000])

        blocks = parse_react_response(response)

        if blocks.get("THOUGHT") and verbose:
            print(f"\nTHOUGHT: {blocks['THOUGHT']}")

        # Execute ACTION if present
        action = blocks.get("ACTION", "")
        if action:
            # Extract commands from the action block
            commands = extract_commands(action)
            if not commands:
                # Treat the whole action as a command if it looks like one
                if action.strip() and not action.strip().startswith("["):
                    commands = [action.strip()]

            for cmd in commands:
                if verbose:
                    print(f"\n[EXEC] {cmd}")

                result = run_tool(cmd, target=task, timeout=get_timeout(cmd))

                obs = f"Command: {cmd}\n"
                if result["success"]:
                    obs += f"Output (truncated): {result['output'][:500]}"
                else:
                    obs += f"Error: {result['output'][:200]}"

                observations.append(obs)
                history.append({"command": cmd, "result": result})

                if verbose:
                    print(f"[RESULT] {'OK' if result['success'] else 'FAILED'}: {result['output'][:200]}")

        # Check for REPORT — final answer
        if blocks.get("REPORT"):
            final_report = blocks["REPORT"]
            if verbose:
                print(f"\n[REPORT]\n{final_report}")
            break

        # If no more actions suggested, wrap up
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
