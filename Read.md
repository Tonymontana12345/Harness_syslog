# Harness Syslog Database

이 문서는 `data/Log/core_one_l_fan_fault.log`를 저장하는 SQLite 데이터베이스의 구조를 설명한다.

## 파일

- 데이터베이스: `data/DB/equipment_logs.db`
- 테이블 정의: `data/DB/schema.sql`
- 로그 적재기: `data/DB/import_log.py`
- 원본 로그: `data/Log/core_one_l_fan_fault.log`

데이터베이스를 다시 만들거나 원본 로그의 변경 사항을 반영하려면 프로젝트 루트에서 다음 명령을 실행한다.

```bash
python3 data/DB/import_log.py
```

같은 원본 파일을 다시 적재하면 해당 파일에서 들어온 기존 행을 먼저 지우고 새로 넣으므로 중복이 생기지 않는다.

## `equipment_logs` 테이블

합성 장비 로그의 한 줄을 한 행으로 저장한다. ISO 8601 형식의 시간은 원문의 시간대 정보까지 유지하기 위해 `TEXT`로 저장한다.

| 컬럼 | 형식 | 설명 |
|---|---|---|
| `id` | INTEGER | 자동 증가 기본 키 |
| `recorded_at` | TEXT | 로그 발생 시각 |
| `level` | TEXT | `INFO`, `WARN`, `ERROR`, `CRITICAL` 로그 수준 |
| `device_id` | TEXT | 장비 식별자 |
| `model` | TEXT | 장비 모델 |
| `state` | TEXT | `PREHEATING`, `PRINTING`, `STOPPING`, `STOPPED` 상태 |
| `event_type` | TEXT | `TELEMETRY`, `FAULT`, `SAFETY_STOP` 등의 이벤트 |
| `error_code` | TEXT | 오류 코드. 정상 로그에서는 `NULL` |
| `fan` | TEXT | 오류 또는 이벤트의 대상 팬 |
| `nozzle_actual_c` | REAL | 노즐 실제 온도(섭씨) |
| `nozzle_target_c` | REAL | 노즐 목표 온도(섭씨) |
| `bed_actual_c` | REAL | 베드 실제 온도(섭씨) |
| `bed_target_c` | REAL | 베드 목표 온도(섭씨) |
| `hotend_fan_rpm` | INTEGER | 핫엔드 팬 회전수 |
| `print_fan_rpm` | INTEGER | 출력물 냉각 팬 회전수 |
| `filament_sensor` | INTEGER | 필라멘트 감지 상태. `1`은 감지됨 |
| `previous_rpm` | INTEGER | RPM 급락 직전 회전수 |
| `job_name` | TEXT | 출력 작업 파일명 |
| `material` | TEXT | 필라멘트 재료 |
| `reason` | TEXT | 안전 정지 등의 발생 사유 |
| `error_count` | INTEGER | 감지 구간 안에서 발생한 오류 횟수 |
| `window_sec` | INTEGER | 반복 오류를 계산한 시간 구간(초) |
| `message` | TEXT | 로그 메시지 |
| `source_file` | TEXT | 데이터를 가져온 로그 파일명 |
| `source_line` | INTEGER | 원본 파일의 줄 번호 |
| `raw_line` | TEXT | 파싱 전 원본 로그 한 줄 |
| `imported_at` | TEXT | DB에 적재한 시각 |

원본 로그에 존재하지 않는 필드는 `NULL`로 저장한다. `raw_line`은 파서 결과를 원문과 대조할 때 사용한다.

## 인덱스

- `idx_equipment_logs_recorded_at`: 시간 범위 조회
- `idx_equipment_logs_device_time`: 특정 장비의 시간 범위 조회
- `idx_equipment_logs_error_time`: 동일 오류의 반복 발생 조회

## 조회 예제

오류 로그만 조회한다.

```sql
SELECT recorded_at, device_id, error_code, hotend_fan_rpm, nozzle_actual_c
FROM equipment_logs
WHERE level = 'ERROR'
ORDER BY recorded_at;
```

10분 이내에 세 번 이상 발생한 오류를 찾는 현재 데모용 조회다.

```sql
SELECT
    device_id,
    error_code,
    COUNT(*) AS occurrence_count,
    MIN(recorded_at) AS first_seen,
    MAX(recorded_at) AS last_seen
FROM equipment_logs
WHERE error_code IS NOT NULL
  AND level = 'ERROR'
GROUP BY device_id, error_code
HAVING COUNT(*) >= 3
   AND (julianday(MAX(recorded_at)) - julianday(MIN(recorded_at))) * 86400 <= 600;
```

현재 합성 데이터에서는 `COREONE-L-01`의 `FAN_RPM_LOW`가 250초 안에 세 번 발생한다.
