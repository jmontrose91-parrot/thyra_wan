"""
Thyra WAN Dorking Filter
Translates plain English commands into precise model instructions.
"""

import re
import json
import sys
from commands.vocabulary import COMMANDS, match_command, list_commands
from prompts.system_prompts import INSTRUCT_SYSTEM, CODER_SYSTEM, WORKFLOW_CONTEXT

INSTRUCT_MODEL = "/home/thyra/models/Qwen3-8B-abliterated-Q4_K_M.gguf"
CODER_MODEL    = "/home/thyra/models/Qwen2.5-Coder-7B-abliterated-Q4_K_M.gguf"
LLAMA_CLI      = "/home/thyra/llama.cpp/build/bin/llama-cli"
LLAMA_SERVER   = "http://localhost:8080"

GPU_LAYERS     = 99
CTX_SIZE       = 4096
TEMP           = 0.3   # low temp for reliable command generation


def _safe(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]", "_", s)


def build_prompt(cmd_name: str, cmd: dict, raw_input: str) -> tuple[str, str, str]:
    """
    Returns (system_prompt, user_prompt, model_path)
    """
    # Extract target from raw input
    alias_match = None
    for alias in cmd["aliases"]:
        if alias in raw_input.lower():
            alias_match = alias
            break

    target = raw_input.lower().replace(alias_match or "", "").strip() if alias_match else raw_input.strip()
    target_safe = _safe(target)

    # Pick model
    if cmd["model"] == "code":
        system = CODER_SYSTEM
        model_path = CODER_MODEL
    else:
        system = INSTRUCT_SYSTEM
        model_path = INSTRUCT_MODEL

    # Build workflow context
    workflow_key = cmd.get("workflow", "")
    context = WORKFLOW_CONTEXT.get(workflow_key, "")
    if context:
        try:
            context = context.format(
                target=target or "TARGET",
                target_safe=target_safe or "TARGET",
                start_freq=target.split("-")[0].strip() if "-" in target else "88M",
                end_freq=target.split("-")[1].strip() if "-" in target else "108M",
                start_freq_mhz=target.split("-")[0].strip().rstrip("M") if "-" in target else "88",
                end_freq_mhz=target.split("-")[1].strip().rstrip("M") if "-" in target else "108",
                channel="6",
                bssid=target,
                url=target,
            )
        except (KeyError, IndexError):
            pass

    user_prompt = context if context else raw_input

    return system, user_prompt, model_path


def query_server(system: str, user: str) -> str:
    """Query llama-server OpenAI-compatible API."""
    import urllib.request
    payload = json.dumps({
        "model": "thyra",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": TEMP,
        "max_tokens": 1024,
        "stream": False,
    }).encode()

    req = urllib.request.Request(
        f"{LLAMA_SERVER}/v1/chat/completions",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"[SERVER ERROR] {e}"


def run_cli(system: str, user: str, model_path: str) -> str:
    """Fall back to llama-cli if server is not running."""
    import subprocess
    prompt = f"<|im_start|>system\n{system}<|im_end|>\n<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n"
    result = subprocess.run(
        [
            "sg", "render", "-c",
            f"export PATH=/usr/local/cuda/bin:$PATH; "
            f"export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH; "
            f"{LLAMA_CLI} -m {model_path} "
            f"--n-gpu-layers {GPU_LAYERS} "
            f"--ctx-size {CTX_SIZE} "
            f"--temp {TEMP} "
            f"-n 512 "
            f"--no-display-prompt "
            f"-p \"{prompt.replace(chr(34), chr(39))}\"",
        ],
        capture_output=True, text=True, timeout=300
    )
    return result.stdout.strip() or result.stderr.strip()


def dork(raw_input: str, use_server: bool = True) -> dict:
    """
    Main entry point. Takes plain English, returns structured response.
    """
    raw_input = raw_input.strip()

    if raw_input.lower() in ("help", "?", "commands", "list"):
        return {"type": "help", "output": list_commands()}

    cmd_name, cmd = match_command(raw_input)
    if not cmd_name:
        # Unknown command — pass raw to instruct model with general SIGINT context
        system = INSTRUCT_SYSTEM
        user = raw_input
        model_path = INSTRUCT_MODEL
    else:
        system, user, model_path = build_prompt(cmd_name, cmd, raw_input)

    if use_server:
        output = query_server(system, user)
    else:
        output = run_cli(system, user, model_path)

    return {
        "type": "response",
        "command": cmd_name,
        "model": "instruct" if model_path == INSTRUCT_MODEL else "code",
        "input": raw_input,
        "output": output,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Thyra WAN Dorking Filter")
    parser.add_argument("command", nargs="*", help="Plain English command")
    parser.add_argument("--no-server", action="store_true", help="Use llama-cli instead of server")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    use_server = not args.no_server

    if args.command:
        raw = " ".join(args.command)
        result = dork(raw, use_server=use_server)
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(result["output"])
        return

    # Interactive REPL
    print("Thyra WAN — Command Interface")
    print('Type "help" for command list, "exit" to quit\n')
    while True:
        try:
            raw = input("thyra> ").strip()
            if not raw:
                continue
            if raw.lower() in ("exit", "quit", "q"):
                break
            result = dork(raw, use_server=use_server)
            if result["type"] == "help":
                print(result["output"])
            else:
                model_tag = f"[{result['model']}]" if result.get("command") else "[instruct]"
                print(f"\n{model_tag} {result['input']}")
                print("─" * 60)
                print(result["output"])
                print()
        except KeyboardInterrupt:
            print()
            break
        except EOFError:
            break


if __name__ == "__main__":
    main()
