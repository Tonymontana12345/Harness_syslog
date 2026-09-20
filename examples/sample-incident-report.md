# 장비 이상 점검 보고서

## 사고 개요

- 장비 ID: COREONE-L-01 (모델 PRUSA_CORE_ONE_L)
- 오류 코드: `FAN_RPM_LOW` (주의: 포트폴리오용 합성 오류 코드이며 공식 매뉴얼 오류 코드가 아니다)
- 반복 조건: 600초 창 내 3회 이상. 조회 결과 3회 (로그 ID 26, 30, 33)
- 발생 구간: 2026-09-20T09:05:00+09:00 ~ 09:09:10+09:00 (250초)
- 결과: 로그 ID 34 (2026-09-20T09:09:11+09:00, CRITICAL, SAFETY_STOP, reason=REPEATED_FAN_FAULT, error_count=3, window_sec=250)로 출력이 정지(STOPPING) 상태가 되었다.
- 조회 범위: 2026-09-20T09:00:00 ~ 09:14:10 (+09:00), 로그 18건 (ID 19~36)

## 로그 근거

| 로그 ID | 시각 | 수준 | 상태/이벤트 | 측정값 | 메시지 |
|---|---|---|---|---|---|
| 23 | 09:02:00 | INFO | PRINTING / TELEMETRY | hotend_fan 7440 rpm, nozzle 215.1C | 정상 기준 |
| 24 | 09:03:00 | INFO | PRINTING / TELEMETRY | hotend_fan 7390 rpm, nozzle 215.3C | - |
| 25 | 09:04:30 | WARN | FAN_RPM_DROP (HOTEND) | 2860 rpm (이전 7390), nozzle 216.2C | - |
| 26 | 09:05:00 | ERROR | FAULT, FAN_RPM_LOW | 1320 rpm, nozzle 217.8C | Hotend fan speed below expected range |
| 27 | 09:05:20 | INFO | FAN_RECOVERED | 7210 rpm, nozzle 216.1C | - |
| 28 | 09:06:00 | INFO | TELEMETRY | 7350 rpm, nozzle 215.4C | - |
| 29 | 09:07:10 | WARN | FAN_RPM_DROP | 2410 rpm (이전 7350), nozzle 216.9C | - |
| 30 | 09:07:30 | ERROR | FAULT, FAN_RPM_LOW | 980 rpm, nozzle 218.5C | Hotend fan speed below expected range |
| 31 | 09:07:50 | INFO | FAN_RECOVERED | 7040 rpm, nozzle 216.8C | - |
| 32 | 09:08:30 | WARN | FAN_RPM_DROP | 1960 rpm (이전 7040), nozzle 218.1C | - |
| 33 | 09:09:10 | ERROR | FAULT, FAN_RPM_LOW | 0 rpm, nozzle 220.4C | Hotend fan stopped |
| 34 | 09:09:11 | CRITICAL | STOPPING / SAFETY_STOP | error_count 3, window_sec 250 | reason REPEATED_FAN_FAULT |
| 35 | 09:09:20 | INFO | STOPPED / TELEMETRY | nozzle 214.2C, bed 59.4C, hotend fan 0 rpm | - |
| 36 | 09:10:00 | INFO | STOPPED / COOLDOWN | nozzle 188.7C, bed 55.8C, hotend fan 0 rpm | - |

로그 사실 요약
- 09:00:30~09:03:00 (ID 20~24) 핫엔드 팬은 약 7180~7440 rpm으로 유지되었다.
- 팬 회전수 저하가 세 차례 반복되었고 최저값이 1320 -> 980 -> 0 rpm으로 낮아졌다 (ID 26, 30, 33).
- 저하 구간의 노즐 온도는 목표 215C보다 높았고 각 오류 시점에 217.8 -> 218.5 -> 220.4C로 상승했다 (ID 26, 30, 33).
- 각 저하 후 20초 내외에 7000 rpm대로 회복되었다 (ID 27, 31). 세 번째는 회복 로그가 조회 범위에 없다.
- 출력 팬(print_fan)은 오류 시점 로그에 값이 없다 (ID 25~33 모두 null).

## 매뉴얼 근거

검색: search_manual, equipment_model=PRUSA_CORE_ONE_L, k=4, use_dictionary=true

| 순위 | 파일 | 페이지 | 관련 내용 | 검색 점수 |
|---|---|---|---|---|
| 1 | prusa3d_manual_core_one_l_101_en.pdf | 64 | 13.8 Fan Error: 프린터가 멈추고 팬 관련 오류가 표시되면 프린트 헤드의 두 팬을 확인하라. 막혀서 회전하지 않을 수 있다. 케이블 연결 등 다른 문제는 help.prusa3d.com 참조 | 0.606469 |
| 2 | prusa3d_manual_core_one_l_101_en.pdf | 60 | 13.1 Error Screens: 치명적 오류 시 오류 화면이 표시되고 QR 코드로 안내 문서에 연결됨. 부품 점검·분해 시 화면 링크 또는 help.prusa3d.com 참조 | 0.539238 |
| 3 | prusa3d_manual_core_one_l_101_en.pdf | 63 | 벨트 장력 등 팬과 직접 관련 없음 | 0.518426 |
| 4 | prusa3d_manual_core_one_l_101_en.pdf | 61 | 첫 레이어 문제 등 팬과 직접 관련 없음 | 0.495611 |

매뉴얼이 기술하는 내용은 위 표의 순위 1, 2 범위에 한정된다. 순위 3, 4는 본 사고와 관련성이 낮아 근거로 사용하지 않는다. (참고: 페이지 64 청크에 "Heating Error" 항목도 있으나 이는 히터·서미스터 연결 점검으로 본 로그와 직접 대응되는지 확인 필요.)

## 점검 절차

매뉴얼 근거가 있는 항목 (우선순위 순)
1. 프린트 헤드의 두 팬을 모두 점검하여 막힘 또는 회전 불가 여부를 확인한다 (prusa3d_manual_core_one_l_101_en.pdf, p.64).
2. 팬 문제가 막힘이 아닌 경우 케이블 연결 등을 help.prusa3d.com의 문서로 확인한다 (p.64).
3. 오류 화면이 표시된 경우 화면 문구와 QR 코드 링크를 따라 안내 문서를 확인한다 (p.60).

매뉴얼에 근거가 없는 항목 (추정, 확인 필요로 분류)
- 추정: 로그상 핫엔드 팬만 저하되었으므로 점검은 핫엔드 팬을 우선하는 것이 합리적이다 (ID 25~33의 fan=HOTEND).
- 추정: 간헐적 저하와 회복 패턴(ID 25~27, 29~31)은 이물질 걸림, 커넥터 접촉 불량 등과 부합할 수 있다. 원인 확정 근거는 없다.
- 확인 필요: 정확한 정상 rpm 기준 범위, `FAN_RPM_LOW` 임계값 (합성 코드로 매뉴얼에 정의 없음).

## 결론 및 한계

확정 가능한 사실
- COREONE-L-01에서 `FAN_RPM_LOW`가 250초 동안 3회 발생했고 (ID 26, 30, 33), 핫엔드 팬 rpm이 악화되어 0 rpm에 이르렀으며, ID 34에서 SAFETY_STOP이 기록되었다.
- 팬 저하 구간에서 노즐 온도가 목표(215C)를 초과했다 (최대 220.4C, ID 33).

추정 (근거 불충분, 확정 아님)
- 핫엔드 팬 이상(물리적 막힘 또는 연결 문제)이 원인일 가능성이 있다. 매뉴얼은 p.64에서 팬 막힘과 케이블 연결을 일반적 점검 대상으로만 언급한다.
- 노즐 온도 상승이 팬 저하의 결과인지 여부는 로그만으로 인과를 확정할 수 없다. 확인 필요.

확인 필요
- 실제 근본 원인 (팬 고장, 막힘, 배선, 제어 측). 현장 점검 결과가 필요하다.
- SAFETY_STOP 정책(3회/창 기준)은 매뉴얼 근거가 없으며 합성 시나리오의 규칙일 수 있다.
- 정지 이후 10:00 이후 로그와 팬 복구 여부는 조회하지 않았다.

한계
- `FAN_RPM_LOW`는 합성 오류 코드로, 매뉴얼 내 대응 코드가 없다. 매뉴얼 근거는 일반 Fan Error 항목(p.64)에 대한 의미적 유사성에 기반한다.
- 매뉴얼 검색은 1회 수행했고 관련 청크는 2개뿐이다.

## 실행 메타데이터

- 사용 MCP 도구: log-db `get_repeated_errors` (device COREONE-L-01, window 600초, minimum_count 3), log-db `get_logs_by_time_range` (2026-09-20T09:00:00+09:00 ~ 09:14:10+09:00, limit 500), manual-rag `search_manual` (k=4, use_dictionary=true, PRUSA_CORE_ONE_L)
- 매뉴얼 버전: 1.01 (검색 결과 메타데이터)
- 입력 토큰 수: 수집되지 않음
- 출력 토큰 수: 수집되지 않음
