# CLAUDE.md — 제조 장비 로그 사고 분석 Harness

## 프로젝트 목적

Prusa CORE One L 장비 로그에서 반복 오류를 확인하고, 로컬 SQLite 이력과 장비 매뉴얼 검색 결과를 근거로 점검 보고서를 작성한다.

## 외부 연결 (MCP)

- `log-db` — 로컬 SQLite 로그를 조회한다.
  - `get_repeated_errors`: 지정 시간 창에서 반복된 오류를 찾는다.
  - `get_logs_by_time_range`: 사고 전후 로그를 시간 범위로 조회한다.
- `manual-rag` — 로컬 Chroma에 저장된 매뉴얼 임베딩을 검색한다.
  - `search_manual`: 오류 코드와 증상을 매뉴얼 용어로 변환하고 관련 청크를 반환한다.

## 기본 분석 순서

1. `log-db`로 반복 오류와 사고 전후 로그를 조회한다.
2. 확인된 오류 코드, 팬 이름, 측정값을 질문으로 만들어 `manual-rag`를 검색한다.
3. 로그 사실과 매뉴얼 근거를 구분해 정리한다.
4. `output/` 아래에 Markdown 점검 보고서를 작성한다.

## 절대 규칙

- 로그에 없는 발생 시각, 측정값, 장비 상태를 만들지 않는다.
- 매뉴얼 검색 결과에 없는 원인이나 정비 절차를 매뉴얼 내용처럼 표현하지 않는다.
- 로그 근거에는 로그 ID와 시각을, 매뉴얼 근거에는 파일명과 페이지 번호를 남긴다.
- 추론은 `추정`으로, 확인할 수 없는 내용은 `확인 필요`로 표시한다.
- 현재 `FAN_RPM_LOW`는 포트폴리오용 합성 오류 코드이며 공식 매뉴얼 코드가 아니다.

## 프로젝트 구조

- `data/DB/equipment_logs.db`: 로그 SQLite DB
- `data/Manual/`: 원본 장비 매뉴얼
- `data/Store/chroma/`: 로컬 벡터 인덱스
- `mcp_servers/`: DB 및 매뉴얼 검색 MCP 서버
- `rag/index_manual.py`: 매뉴얼 청킹·임베딩·인덱싱
- `.claude/skills/`: 재사용 분석 절차
- `.claude/agents/`: 전문 분석 에이전트
- `.claude/hooks/`: 결정론적 보고서 검증
- `output/`: 생성된 점검 보고서
