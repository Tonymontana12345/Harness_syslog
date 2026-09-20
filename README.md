# Harness Syslog

제조 장비의 반복 오류를 SQLite 로그에서 찾고, 장비 매뉴얼 RAG 검색 결과를 근거로 점검 보고서를 작성하는 Claude Code 하네스 예제입니다.

> 이 저장소의 `FAN_RPM_LOW` 오류와 장비 로그는 데모를 위해 만든 합성 데이터입니다. 공식 Prusa 오류 코드나 실제 장비 장애 기록이 아닙니다.
> 자사 장비에 적용하려면 `data/Manual/`에 해당 장비 매뉴얼을 넣고, 로그 DB 구조와 DB MCP를 장비 규격에 맞게 수정해야 합니다.

## 처리 흐름

```mermaid
flowchart LR
    A[합성 장비 로그] --> B[SQLite]
    B --> C[log-db MCP]
    D[장비 매뉴얼 PDF] --> E[청킹 및 OpenAI 임베딩]
    E --> F[로컬 Chroma]
    F --> G[manual-rag MCP]
    C --> H[incident-analyst Agent]
    G --> H
    H --> I[점검 보고서]
    I --> J[규칙 기반 Hook 검증]
```

## 구현 요소

- **MCP**: 시간 범위 로그 조회, 반복 오류 탐지, 매뉴얼 벡터 검색
- **RAG**: PDF 청킹, OpenAI 임베딩, 로컬 Chroma 저장, 키워드 사전 기반 질의 변환
- **Skills**: 사고 근거 수집과 보고서 작성 절차
- **Agent**: DB와 매뉴얼 근거를 결합하는 `incident-analyst`
- **Hooks**: 보고서 근거 검증과 서브에이전트 토큰 사용량 기록
- **Guardrail**: 로그 사실, 매뉴얼 내용, 분석자 추정을 분리

## 프로젝트 구조

```text
.
├── .claude/
│   ├── agents/incident-analyst.md
│   ├── skills/
│   └── hooks/
├── data/
│   ├── DB/
│   ├── Log/
│   ├── Manual/
│   └── Store/chroma/       # 실행 시 생성, Git 제외
├── examples/
├── mcp_servers/
├── output/                 # 실행 시 생성, Git 제외
└── rag/index_manual.py
```

## 준비 사항

- Python 3.10 이상
- [uv](https://docs.astral.sh/uv/)
- Claude Code
- OpenAI API 키
- Prusa CORE One L handbook

Prusa 매뉴얼은 저장소에 재배포하지 않습니다. [Prusa CORE One L 다운로드 페이지](https://help.prusa3d.com/downloads/core-one-l)에서 영문 handbook을 내려받아 다음 경로에 배치하세요.

```text
data/Manual/prusa3d_manual_core_one_l_101_en.pdf
```

현재 코드와의 호환성을 위해 위 파일명을 그대로 사용합니다.

## 실행 방법

저장소 루트에서 환경 파일을 만듭니다.

```bash
cp .env.example .env
```

`.env`에 OpenAI API 키를 입력합니다.

```dotenv
OPENAI_API_KEY=your-api-key
```

합성 로그를 SQLite에 적재합니다.

```bash
python3 data/DB/import_log.py
```

매뉴얼을 청킹하고 로컬 Chroma 인덱스를 생성합니다.

```bash
uv run \
  --with-requirements rag/requirements.txt \
  python rag/index_manual.py --rebuild
```

Claude Code를 실행합니다.

```bash
claude
```

Claude Code에서 `/mcp`를 열고 `log-db`, `manual-rag`를 승인한 뒤 다음 요청을 실행합니다.

```text
@incident-analyst COREONE-L-01에서 600초 안에 3회 이상 반복된 오류를 조사하고, 사고 전후 로그와 장비 매뉴얼을 근거로 점검 보고서를 작성해줘.
```

## 예상 결과

- `FAN_RPM_LOW` 3회 발생 탐지
- 사고 전후 로그와 RPM 변화 수집
- 매뉴얼의 fan error 관련 청크 검색
- 로그 ID와 매뉴얼 페이지가 포함된 점검 보고서 생성
- Hook을 통한 필수 근거 검증

실행 결과 예시는 [sample-incident-report.md](examples/sample-incident-report.md)에서 확인할 수 있습니다.

## Docker로 실행

Docker 버전은 Python과 MCP 의존성을 이미지에 고정합니다. Claude Code와
`.claude/`의 Skill·Agent·Hook은 호스트에서 실행하고, 두 MCP 서버만
컨테이너의 표준 입출력으로 연결합니다. API 키와 매뉴얼 PDF, 로컬 Chroma
인덱스는 이미지에 포함하지 않습니다.

환경 파일을 만들고 OpenAI API 키를 입력합니다.

```bash
cp .env.example .env
```

Prusa 매뉴얼을 아래 경로에 배치한 뒤 이미지를 빌드합니다.

```text
data/Manual/prusa3d_manual_core_one_l_101_en.pdf
```

```bash
docker compose build
docker compose run --rm init-db
docker compose run --rm index-manual
```

Claude Code에서 Docker MCP 설정을 사용하려면 기존 로컬 설정을 보관한 후
Docker 설정으로 교체합니다.

```bash
cp .mcp.json .mcp.local.json
cp .mcp.docker.json .mcp.json
claude
```

Claude Code의 `/mcp`에서 `log-db`와 `manual-rag`를 승인하면 기존과 같은
`@incident-analyst` 요청을 실행할 수 있습니다. 로컬 Python 실행 방식으로
돌아갈 때는 다음 명령을 사용합니다.

```bash
cp .mcp.local.json .mcp.json
```

Docker는 실행 환경을 재현하지만 현재 구조를 완전한 폐쇄망으로 만들지는
않습니다. 매뉴얼 임베딩과 질의 변환은 OpenAI API를 사용하므로 폐쇄망에서는
로컬 임베딩 모델과 로컬 LLM으로 교체해야 합니다.

## 데이터베이스

테이블과 컬럼 설명은 [Read.md](Read.md)를 참고하세요.

## 현재 범위

- MCP 서버는 로컬 `stdio` 방식입니다.
- 문서와 질문 임베딩은 OpenAI API를 사용하고 벡터는 로컬 Chroma에 저장합니다.
- 실제 장비의 지속적인 로그 감시와 시리얼 명령 전송은 아직 포함하지 않습니다.
- 완전한 폐쇄망에서는 OpenAI 임베딩과 Claude Code를 로컬 임베딩 모델 및 로컬 LLM 기반 실행기로 교체해야 합니다.
