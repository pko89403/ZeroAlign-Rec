---
title: "Food Taxonomy Dictionary"
date: 2026-04-08
type: entity
tags: [taxonomy, llm, json, recommendation]
sources: []
---

# Food Taxonomy Dictionary

## 개요

`Food Taxonomy Dictionary`는 전처리된 Food.com recipe metadata를 로컬 LLM으로 분석해 생성하는
도메인 taxonomy 사전이다. `TaxRec`의 domain taxonomy 생성 아이디어를 참고하며, 결과는
`feature_name -> [possible_values]` 구조의 JSON으로 저장된다. 현재 구현은 direct one-shot 전체 입력 대신
bounded sampling과 payload budget을 적용한 hardening 경로를 사용한다.

## 현재 상태

이 프로젝트에는 taxonomy dictionary 생성 코드와 CLI가 구현되어 있다.
입력은 `data/processed/foodcom/recipes.csv`이고, 실행 시 아래 파일이 생성된다.

- `data/processed/foodcom/taxonomy_dictionary/food_taxonomy_dictionary.json`
- `data/processed/foodcom/taxonomy_dictionary/prompt_snapshot.json`
- `data/processed/foodcom/taxonomy_dictionary/taxonomy_report.html`

taxonomy는 단순한 축 목록이 아니라 아래 두 요소를 포함한다.

- feature 이름
- 각 feature의 가능한 값들

현재 구현 검증 상태는 다음과 같다.

- mocked LLM 기반 taxonomy 테스트가 통과했다
- `uv run pytest`, `uv run ruff check .`, `uv run mypy src` 검증이 통과했다
- 실제 MLX LLM으로 end-to-end 생성이 완료되었고 현재 snapshot 기준 입력 규모는 `192`개 recipe다
- 현재 CLI summary는 전체 catalog 수와 실제 prompt 입력 수를 구분해 보여준다
- downstream `Taxonomy Item Structuring` 단계에서 few-shot guidance 및 canonicalization 기준 vocabulary로 재사용된다

## 사용법/설정

### 실행 명령

```bash
uv run sid-reco build-taxonomy-dictionary \
  --recipes-path data/processed/foodcom/recipes.csv \
  --out-dir data/processed/foodcom/taxonomy_dictionary \
  --max-tokens 4096
```

### 동작 규칙

- 입력 필드는 `name`, `description`, `tags`, `ingredients`만 사용한다
- catalog가 `1000`개 이하이면 전체를 prompt에 넣는다
- catalog가 `1000`개를 초과하면 deterministic evenly spaced sampling으로 prompt item을 줄인다
- sampled payload가 너무 크면 payload 길이 상한 안에 들어올 때까지 sample 수를 추가로 줄인다
- 최종 출력은 `dict[str, list[str]]` 구조의 JSON only 결과여야 한다
- feature key와 value는 Python 후처리로 `snake_case` 정규화한다
- JSON 파싱은 첫 complete JSON object 기준으로 수행하고, 실패하면 1회 repair pass를 시도한다
- repair 후에도 invalid JSON이면 실패로 처리한다
- normalization 후 usable feature/value가 하나도 남지 않으면 실패로 처리한다
- `prompt_snapshot.json`에 모델, 파라미터, 전체 item 수, prompt item 수, sampling strategy, dataset payload를 저장한다
- `taxonomy_report.html`은 결과 taxonomy와 snapshot을 사람이 검토하기 위한 standalone 리포트다

## Related

- [Food.com 데이터셋](food-com-dataset.md) — taxonomy dictionary 생성의 원천 데이터
- [개발 환경 세팅](dev-environment.md) — 로컬 MLX LLM과 CLI 실행 환경
- [ADR-001: 개발 환경 및 로컬 추론 스택 결정](../decisions/adr-001-dev-environment.md) — 생성 모델과 개발 스택 결정
- [ADR-004: Taxonomy Dictionary 생성 방식 결정](../decisions/adr-004-taxonomy-dictionary-generation.md) — superseded된 초기 생성 정책
- [ADR-005: Taxonomy Dictionary 생성 hardening 결정](../decisions/adr-005-taxonomy-dictionary-hardening.md) — 현재 bounded input/validation 정책
- [Taxonomy Item Structuring](taxonomy-item-structuring.md) — dictionary를 참조해 item별 TID를 생성하는 downstream 단계
- [SID 컴파일 및 인덱싱](sid-compilation-indexing.md) — structured item taxonomy를 serialization/embedding artifact로 넘기는 다음 단계
- [ADR-006: Strict TID hardening 결정](../decisions/adr-006-strict-tid-hardening.md) — downstream canonicalization과 validator 정책
- [Taxonomy Dictionary 개발 이슈 개요](../overviews/taxonomy-dictionary-development-issues.md) — 구현 및 검증 중 발생한 오류 기록
