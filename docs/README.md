# docs

이 프로젝트의 지식 저장소다. 3-레이어 아키텍처로 구성되어 있다.

## 아키텍처

| 레이어 | 경로 | 소유자 | 역할 |
|--------|------|--------|------|
| 원문 소스 | `sources/` | 사용자 | 큐레이션된 소스 문서 (불변) — 진실의 원천 |
| 위키 | `wiki/` | LLM | 소스를 기반으로 생성된 지식 페이지 |
| 스키마 | [`AGENTS.md`](../AGENTS.md) | 사용자 + LLM | 위키 구조·컨벤션·워크플로 정의 |

## 원문 소스 (`sources/`)

변경 불가. LLM은 읽기만 한다.

| 카테고리 | 내용 |
|----------|------|
| [`papers/`](sources/papers/) | SID·추천 관련 논문 |
| [`datasets/`](sources/datasets/) | 데이터셋 원본 문서·스키마 |
| [`models/`](sources/models/) | 모델 공식 문서·벤치마크 |
| [`experiments/`](sources/experiments/) | 실험 로그·결과 데이터 |

## 위키 (`wiki/`)

LLM이 소유하며 생성·업데이트·교차 참조를 관리한다. 사용자는 읽기만 한다.

- **전체 인덱스**: [`wiki/INDEX.md`](wiki/INDEX.md)

| 카테고리 | 내용 | 페이지 수 |
|----------|------|-----------|
| [`summaries/`](wiki/summaries/) | 소스별 요약 | 0 |
| [`entities/`](wiki/entities/) | 모델·데이터셋·라이브러리 등 구체적 대상 | 4 |
| [`concepts/`](wiki/concepts/) | SID·Training-Free 등 추상 개념 | 0 |
| [`comparisons/`](wiki/comparisons/) | 비교·분석 | 0 |
| [`overviews/`](wiki/overviews/) | 주제별 합성 개요 | 1 |
| [`decisions/`](wiki/decisions/) | ADR (Architecture Decision Record) | 4 |
| [`logs/`](wiki/logs/) | 인제스트 건별 로그 | 0 |

## 오퍼레이션

이 지식 저장소는 3가지 오퍼레이션으로 운영된다. 상세 워크플로는 [`AGENTS.md`](../AGENTS.md) 참조.

| 오퍼레이션 | 설명 |
|------------|------|
| **인제스트** | 새 소스를 `sources/`에 추가 → LLM이 요약·엔티티·개념 페이지 생성/업데이트 |
| **쿼리** | 위키를 대상으로 질문 → LLM이 관련 페이지를 인용하며 답변 합성 |
| **린트** | 위키 상태 점검 → 모순·낡은 정보·고아 페이지·누락 교차 참조 식별 |
