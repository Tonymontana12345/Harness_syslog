#!/usr/bin/env python3
"""Validate incident reports written by Claude Code."""

from __future__ import annotations

import json
import sys
from pathlib import Path


REQUIRED_HEADINGS = (
    "## 사고 개요",
    "## 로그 근거",
    "## 매뉴얼 근거",
    "## 점검 절차",
    "## 결론 및 한계",
)


def main() -> int:
    try:
        event = json.load(sys.stdin)
    except (json.JSONDecodeError, TypeError):
        return 0

    raw_path = event.get("tool_input", {}).get("file_path")
    if not raw_path:
        return 0

    report_path = Path(raw_path).expanduser().resolve()
    project_dir = Path(
        event.get("cwd") or Path(__file__).resolve().parents[2]
    ).resolve()
    output_dir = (project_dir / "output").resolve()

    try:
        relative_path = report_path.relative_to(output_dir)
    except ValueError:
        return 0

    if report_path.suffix.lower() != ".md" or len(relative_path.parts) != 1:
        return 0
    if not report_path.exists():
        return 0

    content = report_path.read_text(encoding="utf-8")
    problems = [
        f"필수 섹션 누락: {heading}"
        for heading in REQUIRED_HEADINGS
        if heading not in content
    ]

    lowered = content.lower()
    if "로그 id" not in lowered and "log_id" not in lowered:
        problems.append("로그 근거에 로그 ID가 없음")
    if "페이지" not in content and "page_number" not in lowered:
        problems.append("매뉴얼 근거에 페이지 번호가 없음")

    if not problems:
        return 0

    print(
        "보고서 근거 검증 실패. 파일을 수정한 뒤 다시 확인하세요: "
        + "; ".join(problems),
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
