---
name: docs-manager
description: "Manage the repository documentation system end-to-end. Use when: ingest new source, query wiki, lint wiki, add wiki page, update INDEX.md, create ADR, sync README.md, sync AGENTS.md, sync .github/copilot-instructions.md, sync .harness/reference/local-adaptation.md, or run a full docs/harness sync after code changes."
argument-hint: "ingest, query, lint, update, or sync — describe what you want to do"
---

# docs-manager

3-레이어 지식 저장소(원문 소스 / 위키 / 스키마)와
저장소 루트 문서/하네스 진입점(`README.md`, `AGENTS.md`,
`.github/copilot-instructions.md`, `.harness/reference/local-adaptation.md`)을 함께 관리하는 스킬이다.
모든 작업은 프로젝트 루트의 `AGENTS.md` 스키마를 따른다.

## When to Use

- 새 소스 문서를 `docs/sources/`에 추가하고 위키에 반영할 때 (인제스트)
- 위키 지식을 기반으로 질문에 답변할 때 (쿼리)
- 위키 상태를 점검하고 문제를 수정할 때 (린트)
- 위키 페이지를 직접 생성/수정할 때
- 코드/CLI/워크플로 변경 후 `README.md`와 하네스 문서를 자동 반영할 때

## Procedure

### Step 0: 스키마 로드

**모든 오퍼레이션의 첫 단계로** 반드시 프로젝트 루트의 `AGENTS.md`를 읽는다.
이 파일에 3-레이어 구조, 6종 페이지 타입별 프론트매터/본문 템플릿, 컨벤션, 워크플로가 정의되어 있다.
스키마가 변경될 수 있으므로 **캐시하지 말고 매번 읽는다**.

sync/update 계열 작업이라면 추가로 아래 파일도 함께 읽는다.

- `README.md`
- `.github/copilot-instructions.md`
- `.harness/reference/local-adaptation.md`
- `docs/wiki/INDEX.md`

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

### Operation: Sync (동기화 루틴)

코드/CLI/워크플로 변경 뒤, 사용자-facing 문서와 하네스 규칙 파일을 한 번에 동기화한다.

1. **변경 범위 파악** — 최근 diff나 변경 파일에서 사용자에게 보이는 워크플로 변화가 있는지 확인한다
2. **README 반영** — quick start, validation, workflow, docs 링크 중 영향받는 섹션을 갱신한다
3. **하네스 반영** — 아래 파일에 새 워크플로/명령/규칙을 반영한다
   - `AGENTS.md`
   - `.github/copilot-instructions.md`
   - `.harness/reference/local-adaptation.md`
4. **위키 영향 분석** — 새 엔티티/개념/ADR가 필요하면 `docs/wiki/`에 추가한다
5. **위키 동기화** — `INDEX.md` + 관련 카테고리 `README.md` + 양방향 `## Related`를 함께 갱신한다
6. **드리프트 점검** — README와 하네스 파일이 현재 구현 명령/경로/모듈 설명과 어긋나지 않는지 확인한다

이 모드는 사실상 이 저장소의 **문서 자동 반영 루틴 기본값**이다.
사용자가 `/docs-manager`만 입력해도 명시적인 다른 모드가 없다면 우선 sync 가능성을 먼저 점검한다.

## Quality Checks

모든 오퍼레이션 완료 후 아래를 확인한다:

- [ ] 모든 위키 페이지에 YAML 프론트매터가 있는가? (title, date, type 필수)
- [ ] `INDEX.md`에 등록된 페이지와 실제 파일이 1:1 매칭되는가?
- [ ] 중복 행이 INDEX.md나 카테고리 README에 없는가?
- [ ] 교차 참조가 양방향으로 설정되어 있는가?
- [ ] `sources` 프론트매터에 올바른 소스 경로가 명시되어 있는가?
- [ ] `README.md`, `AGENTS.md`, `.github/copilot-instructions.md`, `.harness/reference/local-adaptation.md`가 현재 구현과 일치하는가?
- [ ] 새 CLI 명령이나 워크플로가 생겼다면 README와 하네스 둘 다 반영되었는가?

## Key Conventions

- **파일명**: kebab-case (`adr-001-dev-environment.md`, `food-com-dataset.md`)
- **교차 참조**: 상대 경로 마크다운 링크 (`[name](../entities/name.md)`)
- **프론트매터**: 모든 위키 페이지에 필수 (YAML `---` 블록)
- **인덱스 동기화**: 페이지 생성/삭제 시 `INDEX.md` + 카테고리 `README.md` 동시 업데이트
- **사실 기반**: 소스에 있는 내용만 작성, 추측 금지
- **한국어**: 문서는 한국어로 작성
- **하네스 동기화**: 구현 흐름이 바뀌면 `README.md` + `AGENTS.md` + `.github/copilot-instructions.md` + `.harness/reference/local-adaptation.md`를 함께 점검

## Operation: Backup (백업)

위키 전체를 스냅샷으로 백업한다.

1. **현재 상태 확인** — `docs/wiki/INDEX.md`에서 전체 페이지 목록 파악
2. **백업 생성** — `docs/wiki/` 디렉터리 전체를 타임스탬프 기반 아카이브로 복사
   ```bash
   tar czf docs/wiki-backup-YYYY-MM-DD.tar.gz docs/wiki/
   ```
3. **검증** — 아카이브 내 파일 수가 INDEX.md 등록 수 + README/INDEX 파일 수와 일치하는지 확인
4. **보고** — 백업 파일 경로, 포함된 페이지 수, 파일 크기 보고
