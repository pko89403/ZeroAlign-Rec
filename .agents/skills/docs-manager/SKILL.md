---
name: docs-manager
description: "Manage 3-layer knowledge base (sources/wiki/schema). Use when: ingest new source, query wiki, lint wiki, add wiki page, update INDEX.md, create ADR, create summary, create entity page, create concept page, run wiki lint, check cross-references, add source document. Reads AGENTS.md for schema rules."
argument-hint: "ingest, query, or lint — describe what you want to do"
---

# docs-manager

3-레이어 지식 저장소(원문 소스 / 위키 / 스키마)를 관리하는 스킬이다.
모든 작업은 프로젝트 루트의 `AGENTS.md` 스키마를 따른다.

## When to Use

- 새 소스 문서를 `docs/sources/`에 추가하고 위키에 반영할 때 (인제스트)
- 위키 지식을 기반으로 질문에 답변할 때 (쿼리)
- 위키 상태를 점검하고 문제를 수정할 때 (린트)
- 위키 페이지를 직접 생성/수정할 때

## Procedure

### Step 0: 스키마 로드

**모든 오퍼레이션의 첫 단계로** 반드시 프로젝트 루트의 `AGENTS.md`를 읽는다.
이 파일에 3-레이어 구조, 6종 페이지 타입별 프론트매터/본문 템플릿, 컨벤션, 워크플로가 정의되어 있다.
스키마가 변경될 수 있으므로 **캐시하지 말고 매번 읽는다**.

### Operation: Ingest (인제스트)

새 소스를 원문 컬렉션에 추가하고 위키에 반영한다.

1. **소스 확인** — 사용자가 지정한 `docs/sources/{category}/` 파일을 읽는다
2. **요약 페이지 생성** — `docs/wiki/summaries/<slug>.md` 작성 (Summary 타입)
3. **영향 분석** — `docs/wiki/INDEX.md`를 읽고 영향받는 기존 페이지를 식별한다
4. **기존 페이지 업데이트** — 관련 페이지에 새 소스 내용 반영, `sources` 프론트매터에 경로 추가
5. **신규 페이지 생성** — 새로운 엔티티/개념이 발견되면 해당 타입 페이지 생성
6. **교차 참조 갱신** — 새 페이지 ↔ 기존 페이지 간 양방향 링크 추가
7. **인덱스 업데이트** — `INDEX.md` + 관련 카테고리 `README.md` 동시 업데이트
8. **인제스트 로그** — `docs/wiki/logs/ingest-YYYY-MM-DD-<slug>.md` 작성

**주의**: 단일 소스가 10~15개 위키 페이지에 영향 가능. 중복 행 삽입에 주의한다.

### Operation: Query (쿼리)

위키를 대상으로 질문에 답변한다.

1. **질문 분석** — 관련 키워드, 개념, 엔티티 식별
2. **페이지 탐색** — `INDEX.md` 참조 → 관련 위키 페이지 읽기
3. **답변 합성** — 관련 페이지를 인용하며 답변 구성 (`[페이지](경로)에 따르면 ...`)
4. **출력 형태 선택** — 마크다운, 비교 표, Marp 슬라이드, matplotlib 차트 등
5. **(선택) 위키 저장** — 사용자 승인 후 overview/comparison 등으로 저장

### Operation: Lint (린트)

위키 상태를 점검하고 문제를 보고한다.

1. **페이지 목록 로드** — `INDEX.md`에서 전체 목록 파악
2. **전수 스캔** — 모든 위키 페이지 읽기
3. **체크리스트 점검**:
   - `[HIGH]` 모순 검출 — 페이지 간 상충하는 주장
   - `[HIGH]` 낡은 정보 — 최신 소스에 의해 대체된 주장
   - `[MEDIUM]` 고아 페이지 — 인바운드 링크 없는 페이지
   - `[MEDIUM]` 누락 개념 — 참조되지만 자체 페이지 없는 개념
   - `[LOW]` 누락 교차 참조 — 관련 페이지 간 빠진 링크
   - `[LOW]` 데이터 공백 — 추가 소스로 채울 수 있는 빈 영역
4. **보고서 출력** — 심각도별 표 + 제안 조치
5. **(선택) 자동 수정** — 사용자 승인 후 교차 참조, 인덱스 갱신 등 적용

## Quality Checks

모든 오퍼레이션 완료 후 아래를 확인한다:

- [ ] 모든 위키 페이지에 YAML 프론트매터가 있는가? (title, date, type 필수)
- [ ] `INDEX.md`에 등록된 페이지와 실제 파일이 1:1 매칭되는가?
- [ ] 중복 행이 INDEX.md나 카테고리 README에 없는가?
- [ ] 교차 참조가 양방향으로 설정되어 있는가?
- [ ] `sources` 프론트매터에 올바른 소스 경로가 명시되어 있는가?

## Key Conventions

- **파일명**: kebab-case (`adr-001-dev-environment.md`, `food-com-dataset.md`)
- **교차 참조**: 상대 경로 마크다운 링크 (`[name](../entities/name.md)`)
- **프론트매터**: 모든 위키 페이지에 필수 (YAML `---` 블록)
- **인덱스 동기화**: 페이지 생성/삭제 시 `INDEX.md` + 카테고리 `README.md` 동시 업데이트
- **사실 기반**: 소스에 있는 내용만 작성, 추측 금지
- **한국어**: 문서는 한국어로 작성

## Operation: Backup (백업)

위키 전체를 스냅샷으로 백업한다.

1. **현재 상태 확인** — `docs/wiki/INDEX.md`에서 전체 페이지 목록 파악
2. **백업 생성** — `docs/wiki/` 디렉터리 전체를 타임스탬프 기반 아카이브로 복사
   ```bash
   tar czf docs/wiki-backup-YYYY-MM-DD.tar.gz docs/wiki/
   ```
3. **검증** — 아카이브 내 파일 수가 INDEX.md 등록 수 + README/INDEX 파일 수와 일치하는지 확인
4. **보고** — 백업 파일 경로, 포함된 페이지 수, 파일 크기 보고
