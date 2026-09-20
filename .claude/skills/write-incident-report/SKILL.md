---
name: write-incident-report
description: Writes a concise equipment inspection report from an Evidence Bundle. Use after log and manual evidence has been collected.
argument-hint: "[output filename]"
---

# 점검 보고서 작성

입력된 Evidence Bundle만 근거로 보고서를 작성한다. 기본 저장 경로는 `output/incident-report-YYYYMMDD-HHMMSS.md`이다.

## 필수 구성

```markdown
# 장비 이상 점검 보고서

## 사고 개요

## 로그 근거

## 매뉴얼 근거

## 점검 절차

## 결론 및 한계

## 실행 메타데이터
```

## 작성 규칙

- 사고 개요에는 장비 ID, 오류 코드, 반복 조건, 발생 구간을 쓴다.
- 로그 근거에는 반드시 로그 ID와 시각을 쓴다.
- 매뉴얼 근거에는 반드시 원본 파일명과 페이지 번호를 쓴다.
- 점검 절차는 매뉴얼 근거가 있는 항목을 우선순위 순으로 쓴다.
- 원인 확정과 가능성 추정을 명확히 구분한다.
- 근거가 부족한 항목은 `확인 필요`로 남긴다.
- 합성 오류 코드라는 사실을 명시한다.
- 실행 메타데이터에는 사용한 MCP 도구와 모델이 제공한 경우에만 입력·출력 토큰 수를 기록한다. 토큰 수를 알 수 없으면 `수집되지 않음`이라고 쓴다.
