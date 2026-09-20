from __future__ import annotations

import sqlite3
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LOG_PATH = PROJECT_ROOT / "data" / "Log" / "core_one_l_fan_fault.log"
DB_PATH = PROJECT_ROOT / "data" / "DB" / "equipment_logs.db"
SCHEMA_PATH = PROJECT_ROOT / "data" / "DB" / "schema.sql"


COLUMN_MAP = {
    "LEVEL": "level",
    "DEVICE": "device_id",
    "MODEL": "model",
    "STATE": "state",
    "EVENT": "event_type",
    "ERROR_CODE": "error_code",
    "FAN": "fan",
    "NOZZLE_ACT_C": "nozzle_actual_c",
    "NOZZLE_TARGET_C": "nozzle_target_c",
    "BED_ACT_C": "bed_actual_c",
    "BED_TARGET_C": "bed_target_c",
    "HOTEND_FAN_RPM": "hotend_fan_rpm",
    "PRINT_FAN_RPM": "print_fan_rpm",
    "FILAMENT_SENSOR": "filament_sensor",
    "PREVIOUS_RPM": "previous_rpm",
    "JOB": "job_name",
    "MATERIAL": "material",
    "REASON": "reason",
    "ERROR_COUNT": "error_count",
    "WINDOW_SEC": "window_sec",
    "MESSAGE": "message",
}

FLOAT_FIELDS = {
    "nozzle_actual_c",
    "nozzle_target_c",
    "bed_actual_c",
    "bed_target_c",
}

INTEGER_FIELDS = {
    "hotend_fan_rpm",
    "print_fan_rpm",
    "filament_sensor",
    "previous_rpm",
    "error_count",
    "window_sec",
}


def convert_value(column: str, value: str):
    value = value.strip().strip('"')
    if column in FLOAT_FIELDS:
        return float(value)
    if column in INTEGER_FIELDS:
        return int(value)
    return value


def parse_log_line(line: str, source_line: int) -> dict | None:
    stripped = line.strip()
    if not stripped or stripped.startswith("#"):
        return None

    parts = [part.strip() for part in stripped.split(" | ")]
    record = {
        "recorded_at": parts[0],
        "source_file": LOG_PATH.name,
        "source_line": source_line,
        "raw_line": stripped,
    }

    for part in parts[1:]:
        if "=" not in part:
            continue
        key, value = part.split("=", 1)
        column = COLUMN_MAP.get(key)
        if column:
            record[column] = convert_value(column, value)

    required = ("recorded_at", "level", "device_id")
    missing = [field for field in required if not record.get(field)]
    if missing:
        raise ValueError(f"line {source_line}: missing required fields {missing}")

    return record


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    records = []
    for line_number, line in enumerate(LOG_PATH.read_text(encoding="utf-8").splitlines(), 1):
        record = parse_log_line(line, line_number)
        if record:
            records.append(record)

    columns = [
        "recorded_at",
        "level",
        "device_id",
        "model",
        "state",
        "event_type",
        "error_code",
        "fan",
        "nozzle_actual_c",
        "nozzle_target_c",
        "bed_actual_c",
        "bed_target_c",
        "hotend_fan_rpm",
        "print_fan_rpm",
        "filament_sensor",
        "previous_rpm",
        "job_name",
        "material",
        "reason",
        "error_count",
        "window_sec",
        "message",
        "source_file",
        "source_line",
        "raw_line",
    ]
    placeholders = ", ".join("?" for _ in columns)
    insert_sql = (
        f"INSERT INTO equipment_logs ({', '.join(columns)}) "
        f"VALUES ({placeholders})"
    )

    with sqlite3.connect(DB_PATH) as connection:
        connection.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
        connection.execute(
            "DELETE FROM equipment_logs WHERE source_file = ?",
            (LOG_PATH.name,),
        )
        connection.executemany(
            insert_sql,
            [[record.get(column) for column in columns] for record in records],
        )
        connection.commit()

    print(f"Imported {len(records)} rows into {DB_PATH}")


if __name__ == "__main__":
    main()
