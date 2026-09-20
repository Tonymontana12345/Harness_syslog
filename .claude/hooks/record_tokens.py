#!/usr/bin/env python3
"""Record per-step token usage of a finished subagent and rebuild the dashboard.

Runs as a SubagentStop hook (event JSON on stdin). It can also be run by hand
to backfill a run:

    record_tokens.py --transcript PATH [--agent-id ID] [--agent-type TYPE]

Outputs (under <project>/Token/):
    token_usage.json  accumulated runs, upserted by agent id
    dashboard.html    self-contained page with the JSON embedded
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOKEN_FIELDS = (
    ("input", "input_tokens"),
    ("output", "output_tokens"),
    ("cache_creation", "cache_creation_input_tokens"),
    ("cache_read", "cache_read_input_tokens"),
)


def parse_transcript(path: Path) -> list[dict]:
    """Return one step per assistant message that carries usage."""
    by_id: dict[str, dict] = {}
    order: list[str] = []
    for index, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = entry.get("message")
        if not isinstance(message, dict) or message.get("role") != "assistant":
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        content = message.get("content")
        tools = [
            block.get("name")
            for block in content
            if isinstance(block, dict) and block.get("type") == "tool_use"
        ] if isinstance(content, list) else []
        key = message.get("id") or f"line-{index}"
        if key not in by_id:
            order.append(key)
        by_id[key] = {
            "timestamp": entry.get("timestamp"),
            "tools": tools,
            **{name: int(usage.get(src) or 0) for name, src in TOKEN_FIELDS},
        }
    steps = [by_id[key] for key in order]
    for number, step in enumerate(steps, start=1):
        step["n"] = number
    return steps


def totals(steps: list[dict]) -> dict:
    return {name: sum(s[name] for s in steps) for name, _ in TOKEN_FIELDS}


def load_store(path: Path) -> dict:
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data.get("runs"), list):
                return data
        except json.JSONDecodeError:
            pass
    return {"runs": []}


def render_dashboard(store: dict, template: str) -> str:
    payload = json.dumps(store, ensure_ascii=False).replace("</", "<\\/")
    return template.replace("__DATA__", payload)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transcript")
    parser.add_argument("--agent-id")
    parser.add_argument("--agent-type")
    parser.add_argument("--project-dir")
    args = parser.parse_args()

    event: dict = {}
    if not args.transcript:
        try:
            event = json.load(sys.stdin)
        except (json.JSONDecodeError, TypeError):
            return 0

    transcript = args.transcript or event.get("agent_transcript_path")
    if not transcript:
        return 0
    transcript_path = Path(transcript).expanduser()
    if not transcript_path.exists():
        return 0

    project_dir = Path(
        args.project_dir
        or event.get("cwd")
        or Path(__file__).resolve().parents[2]
    ).resolve()
    token_dir = project_dir / "Token"
    token_dir.mkdir(exist_ok=True)

    steps = parse_transcript(transcript_path)
    if not steps:
        return 0

    agent_id = args.agent_id or event.get("agent_id") or transcript_path.stem
    run = {
        "run_id": agent_id,
        "agent_type": args.agent_type or event.get("agent_type") or "unknown",
        "session_id": event.get("session_id"),
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "started": steps[0]["timestamp"],
        "ended": steps[-1]["timestamp"],
        "steps": steps,
        "totals": totals(steps),
    }

    json_path = token_dir / "token_usage.json"
    store = load_store(json_path)
    store["runs"] = [r for r in store["runs"] if r.get("run_id") != agent_id]
    store["runs"].append(run)
    json_path.write_text(
        json.dumps(store, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    template = (Path(__file__).with_name("dashboard_template.html")).read_text(
        encoding="utf-8"
    )
    (token_dir / "dashboard.html").write_text(
        render_dashboard(store, template), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
