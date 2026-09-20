CREATE TABLE IF NOT EXISTS equipment_logs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    recorded_at         TEXT NOT NULL,
    level               TEXT NOT NULL,
    device_id           TEXT NOT NULL,
    model               TEXT,
    state               TEXT,
    event_type          TEXT,
    error_code          TEXT,
    fan                 TEXT,
    nozzle_actual_c     REAL,
    nozzle_target_c     REAL,
    bed_actual_c        REAL,
    bed_target_c        REAL,
    hotend_fan_rpm      INTEGER,
    print_fan_rpm       INTEGER,
    filament_sensor     INTEGER,
    previous_rpm        INTEGER,
    job_name            TEXT,
    material            TEXT,
    reason              TEXT,
    error_count         INTEGER,
    window_sec          INTEGER,
    message             TEXT,
    source_file         TEXT NOT NULL,
    source_line         INTEGER NOT NULL,
    raw_line            TEXT NOT NULL,
    imported_at         TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (source_file, source_line)
);

CREATE INDEX IF NOT EXISTS idx_equipment_logs_recorded_at
    ON equipment_logs (recorded_at);

CREATE INDEX IF NOT EXISTS idx_equipment_logs_device_time
    ON equipment_logs (device_id, recorded_at);

CREATE INDEX IF NOT EXISTS idx_equipment_logs_error_time
    ON equipment_logs (error_code, recorded_at);
