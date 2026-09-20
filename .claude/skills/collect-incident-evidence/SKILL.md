---
name: collect-incident-evidence
description: Collects grounded evidence for a manufacturing equipment incident from the log DB and manual RAG MCP tools. Use when an error repeats or the user asks to investigate equipment logs.
argument-hint: "[device_id] [window_seconds] [minimum_count]"
---

# 사고 근거 수집

사용자가 별도로 지정하지 않으면 다음 기본값을 사용한다.

- `device_id`: `COREONE-L-01`
- `window_seconds`: `600`
- `minimum_count`: `3`

## 절차

1. `log-db`의 `get_repeated_errors`를 호출해 반복 오류를 확인한다.
2. 반복 오류가 없으면 그 사실을 알리고 분석을 중단한다.
3. 각 반복 오류의 `first_seen`부터 `last_seen`까지를 기준으로 사고 전후가 포함되도록 시간 범위를 정한다. 가능한 경우 앞뒤 5분을 포함한다.
4. `log-db`의 `get_logs_by_time_range`로 해당 범위의 로그를 조회한다.
5. 오류 코드, 장비 모델, 팬 이름, RPM 변화, 정지 사유를 포함한 검색 질문을 만든다.
6. `manual-rag`의 `search_manual`을 `k=4`, `use_dictionary=true`로 호출한다.
7. 아래 형식의 Evidence Bundle을 반환한다.

## Evidence Bundle 형식

```markdown
### 감지 조건
- 장비 ID:
- 오류 코드:
- 반복 횟수:
- 감지 시간 창:
- 최초/최종 발생 시각:

### 로그 근거
| 로그 ID | 시각 | 수준 | 상태/이벤트 | 측정값 | 메시지 |
|---|---|---|---|---|---|

### 매뉴얼 근거
| 순위 | 파일 | 페이지 | 관련 내용 | 검색 점수 |
|---|---|---|---|---|

### 사실과 추정
- 확인된 사실:
- 매뉴얼이 제시하는 점검 항목:
- 추정:
- 확인 필요:
```

## 제약

- MCP 결과에 없는 값을 채우지 않는다.
- 매뉴얼 청크의 의미를 과장하지 않는다.
- `FAN_RPM_LOW` 자체가 공식 매뉴얼 오류 코드라고 쓰지 않는다.
- 매뉴얼 페이지는 MCP가 반환한 `page_number`를 사용한다.
