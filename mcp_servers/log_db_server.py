from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

from mcp.server import MCPServer


SERVER_NAME = "log-db"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "DB" / "equipment_logs.db"
MAX_LOG_ROWS = 500

mcp = MCPServer(SERVER_NAME)


def _parse_iso8601(value: str, field_name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(
            f"{field_name} must be an ISO 8601 timestamp: {value}"
        ) from exc

    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone offset")
    return parsed


def _connect_read_only() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {DB_PATH}")

    connection = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def query_logs_by_time_range(
    device_id: str,
    start_time: str,
    end_time: str,
    limit: int = 200,
) -> dict[str, Any]:
    start = _parse_iso8601(start_time, "start_time")
    end = _parse_iso8601(end_time, "end_time")
    if start > end:
        raise ValueError("start_time must be earlier than or equal to end_time")
    if not 1 <= limit <= MAX_LOG_ROWS:
        raise ValueError(f"limit must be between 1 and {MAX_LOG_ROWS}")

    sql = """
        SELECT
            id,
            recorded_at,
            level,
            device_id,
            model,
            state,
            event_type,
            error_code,
            fan,
            nozzle_actual_c,
            nozzle_target_c,
            bed_actual_c,
            bed_target_c,
            hotend_fan_rpm,
            print_fan_rpm,
            filament_sensor,
            previous_rpm,
            reason,
            error_count,
            window_sec,
            message
        FROM equipment_logs
        WHERE device_id = ?
          AND recorded_at BETWEEN ? AND ?
        ORDER BY recorded_at
        LIMIT ?
    """

    with _connect_read_only() as connection:
        rows = connection.execute(
            sql,
            (device_id, start_time, end_time, limit),
        ).fetchall()

    return {
        "device_id": device_id,
        "start_time": start_time,
        "end_time": end_time,
        "log_count": len(rows),
        "logs": [dict(row) for row in rows],
    }


def query_repeated_errors(
    device_id: str,
    window_seconds: int = 600,
    minimum_count: int = 3,
) -> dict[str, Any]:
    if not 1 <= window_seconds <= 86_400:
        raise ValueError("window_seconds must be between 1 and 86400")
    if not 2 <= minimum_count <= 100:
        raise ValueError("minimum_count must be between 2 and 100")

    sql = """
        SELECT id, recorded_at, error_code
        FROM equipment_logs
        WHERE device_id = ?
          AND level = 'ERROR'
          AND error_code IS NOT NULL
        ORDER BY error_code, recorded_at
    """

    with _connect_read_only() as connection:
        rows = connection.execute(sql, (device_id,)).fetchall()

    events_by_code: dict[str, list[sqlite3.Row]] = defaultdict(list)
    for row in rows:
        events_by_code[row["error_code"]].append(row)

    repeated_errors = []
    for error_code, events in events_by_code.items():
        left = 0
        best_window: tuple[int, int] | None = None

        for right, event in enumerate(events):
            right_time = _parse_iso8601(event["recorded_at"], "recorded_at")
            while left <= right:
                left_time = _parse_iso8601(
                    events[left]["recorded_at"],
                    "recorded_at",
                )
                if (right_time - left_time).total_seconds() <= window_seconds:
                    break
                left += 1

            count = right - left + 1
            if count >= minimum_count:
                if best_window is None or count > best_window[1] - best_window[0] + 1:
                    best_window = (left, right)

        if best_window is None:
            continue

        first_index, last_index = best_window
        selected = events[first_index : last_index + 1]
        first_seen = selected[0]["recorded_at"]
        last_seen = selected[-1]["recorded_at"]
        elapsed_seconds = int(
            (
                _parse_iso8601(last_seen, "recorded_at")
                - _parse_iso8601(first_seen, "recorded_at")
            ).total_seconds()
        )

        repeated_errors.append(
            {
                "error_code": error_code,
                "count": len(selected),
                "first_seen": first_seen,
                "last_seen": last_seen,
                "elapsed_seconds": elapsed_seconds,
                "log_ids": [row["id"] for row in selected],
            }
        )

    return {
        "device_id": device_id,
        "window_seconds": window_seconds,
        "minimum_count": minimum_count,
        "repeated_errors": repeated_errors,
    }


@mcp.tool()
def get_logs_by_time_range(
    device_id: str,
    start_time: str,
    end_time: str,
    limit: int = 200,
) -> dict[str, Any]:
    """Return equipment logs for one device within an ISO 8601 time range.

    Args:
        device_id: Equipment identifier, for example COREONE-L-01.
        start_time: Inclusive range start with timezone offset.
        end_time: Inclusive range end with timezone offset.
        limit: Maximum number of rows to return, from 1 to 500.
    """
    return query_logs_by_time_range(device_id, start_time, end_time, limit)


@mcp.tool()
def get_repeated_errors(
    device_id: str,
    window_seconds: int = 600,
    minimum_count: int = 3,
) -> dict[str, Any]:
    """Find error codes repeated enough times inside a sliding time window.

    Args:
        device_id: Equipment identifier, for example COREONE-L-01.
        window_seconds: Size of the sliding detection window in seconds.
        minimum_count: Minimum error occurrences required in the window.
    """
    return query_repeated_errors(device_id, window_seconds, minimum_count)


if __name__ == "__main__":
    mcp.run(transport="stdio")
