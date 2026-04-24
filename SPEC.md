# 스펙: SKI-10 — Query-SID 런타임 재현

## 가정 (Assumptions I'm Making)

1. 이 기능은 기존 Phase 1 `compile-sid-index`와 Phase 2 `recommend` 파이프라인 위에서 동작한다. 둘 다 이미 구현되어 운영 중이다.
2. `train_codebooks`가 학습한 residual K-means quantizer(`TrainedResidualCodebooks`)는 현재 할당 직후 버려진다. 이 스펙은 이 quantizer에 1급 저장과 런타임 재사용을 부여한다.
3. 런타임 query는 catalog item과 **같은 SID 공간**에 떨어져야 한다 — 같은 codebook, 같은 정규화 규칙, 같은 residual 시퀀스. 그렇지 않으면 `query_sid`를 item SID와 비교할 수 없다.
4. `apps/demo`는 실제 Phase 1 artifact를 읽지 않는 브라우저-로컬 mock 파이프라인이다. 이 스펙은 데이터 소스가 아니라 계약 shape만 조정한다.
5. 기존 `id_map.jsonl`은 이미 item별 `sid_path`를 기록한다. 런타임은 현재 `sid_string`만 로드한다. 이 스펙은 `sid_path`를 검증하고 파이프라인 전체에 보존한다.
6. 이 스펙은 retrieval score, adaptive radius, bootstrap rerank 정책, confidence aggregation을 수정하지 않는다. 이들은 명시적으로 범위 밖이고 후속 이슈로 남긴다.
7. 분할 PR보다 단일 PR을 선호한다 — 타입 리팩터와 런타임 재현은 같은 주제다.
8. 기본 출력 디렉터리 `data/processed/foodcom/sid_index/`는 이미 `data/processed/*`로 `.gitignore` 처리되어 있다. 이 스펙은 새 gitignore 규칙을 추가하지 않는다.

## 목표 (Objective)

런타임 추천 query를 retrieval 대상 catalog item과 재현 가능하게 같은 계층적 SID 공간에 떨어지게 만들고, 그 할당을 추천 응답의 1급 필드로 노출한다.

구체적으로:

1. `compile-sid-index`가 학습한 residual K-means quantizer를 런타임 artifact(`residual_codebooks.npz` + `residual_codebooks_manifest.json`)로 저장한다.
2. `recommend` 내부에서 이 quantizer를 로드하고, taxonomy-aligned query 벡터를 **컴파일 시점과 완전히 동일한 residual 정규화 규칙**으로 계층적 SID path에 할당한다.
3. 결과 `query_sid`를 `SemanticSearchResult`, `RecommendationResponse`, `recommend` CLI, `apps/demo` mock 파이프라인 shape에 노출한다.
4. 그 과정에서 SID 타입 레이어를 정리해 `ItemSID` / `QuerySID` 두 구체 타입만 남기고, 중복된 `CompiledSIDItems` 번들 타입과 장황한 함수명을 제거한다.

제품 효과는 모든 추천 응답이 query 자신의 SID 좌표를 함께 가지고 나가는 것이다. 이는 향후 query-SID locality를 활용하는 검색 반경·그룹 confidence·rerank prior 작업(명시적으로 유보)의 기초가 된다.

## 비목표 (Non-Goals)

이 스펙은 **다음을 포함하지 않는다**:

- `query_sid` 기반 FAISS score·retrieval `k`·survivor cap 조정
- `query_sid` 근접성에 연동된 adaptive 검색 반경
- SID-group confidence aggregation
- bootstrap rerank pass 수·selection size·prompt 내용 변경
- grounding·최종 payload 조립 변경
- 어떤 모델의 학습 혹은 파인튜닝
- `apps/demo`가 실제 artifact를 소비하도록 재작성
- `TrainedResidualCodebooks`를 `SIDSpace`로 리네임 (유보 — 본 범위에서 구조적 이득 없이 비용만 발생)
- `compile-sid-index` CLI 명령 이름 변경 (사용자 워크플로 영향)

## 타입 시스템 리팩터 (Type System Refactor)

런타임 작업의 구조적 전제 조건이며 같은 PR에 묶는다.

### Before

```
TrainedResidualCodebooks        # quantizer
CompiledSIDItem                 # recipe_id + sid_path + sid_string
CompiledSIDItems                # items + branching_factor + depth + embedding_dim + levels
                                #   ^ 4개 필드가 TrainedResidualCodebooks와 중복
```

### After

```
TrainedResidualCodebooks        # quantizer — 유지, 저장 대상으로 승격
ItemSID                         # recipe_id + sid_path + sid_string   (CompiledSIDItem 대체)
QuerySID                        # sid_path + sid_string               (신규)
# CompiledSIDItems 삭제.
# compile_residual_kmeans 편의 래퍼 삭제.
# base dataclass 없음 — 두 타입 사이의 2필드 중복은 수용(4줄).
```

근거:

- `item`과 `query`는 실제 코드에서 공통 호출자가 없다. 두 타입을 `isinstance(x, SomeBase)`로 묶어야 할 자리가 현재도 이번 범위에서도 없으므로 base dataclass는 비용 대비 이득이 없다.
- 삭제되는 `CompiledSIDItems` 번들 타입은 `TrainedResidualCodebooks`가 이미 소유한 4개 필드를 중복 보관한다. 제거하면 공간-shape 메타데이터의 단일 진실 원천이 quantizer로 집중된다.
- 편의 래퍼는 호출처가 두 곳(CLI + 테스트 한 곳)이다. 두 줄의 명시적 호출로 대체하는 편이 codebook 반환값을 숨기는 얇은 indirection을 유지하는 것보다 저렴하다.
- 함수 이름에서 `_trained_`, `_residual_`, `assign_*_to_sid` 같은 장황한 수식어는 `TrainedResidualCodebooks` 타입 이름이 이미 전달하므로 제거한다. 남는 이름은 동사(`train`/`write`/`load`/`build`) + 대상으로 간결하다.

Python 측 제약:

- `ItemSID`와 `QuerySID`는 각각 독립 `@dataclass(frozen=True, slots=True)`이며 상속을 쓰지 않는다. frozen+slots 상속의 함정을 원천 배제한다.
- `CompiledSIDItem` / `CompiledSIDItems` 삭제는 hard rename이다 — backward-compat alias 없음. 저장소의 "backwards-compat 우회 금지" 관례에 따른다.

## 런타임 artifact 계약 (Runtime Artifact Contract)

모든 신규 artifact는 기존 `sid_index_dir`(기본 `data/processed/foodcom/sid_index/`) 안에 저장한다.

### `residual_codebooks.npz`

NumPy archive, float32. 키:

- `branching_factor` — scalar int32
- `depth` — scalar int32
- `embedding_dim` — scalar int32
- `normalize_residuals` — scalar int32 (0/1)
- `level_{i}_centroids` (`i ∈ 1..depth`) — shape `(cluster_count_i, embedding_dim)`
- `level_{i}_cluster_sizes` (`i ∈ 1..depth`) — shape `(cluster_count_i,)` int32
- `level_{i}_iteration_count` (`i ∈ 1..depth`) — scalar int32
- `level_{i}_inertia` (`i ∈ 1..depth`) — scalar float32

단일 NPZ 레이아웃은 quantizer를 한 파일로 유지하면서 `ResidualKMeansLevel`이 이미 가진 per-level replay 메타데이터를 보존한다.

### `residual_codebooks_manifest.json`

작고 사람이 읽기 좋은 JSON(정렬):

```json
{
  "branching_factor": 256,
  "depth": 3,
  "embedding_dim": 3584,
  "normalize_residuals": true,
  "level_cluster_counts": [256, 256, 256],
  "codebooks_path": "residual_codebooks.npz"
}
```

`codebooks_path`는 **`sid_index_dir` 기준 상대 파일명**이다. 절대경로 금지.

### 상위 `manifest.json` 갱신

기존 키는 모두 유지. 신규 키를 append만 한다:

- `normalize_residuals` (bool)
- `codebooks_path` (상대 파일명, 예: `"residual_codebooks.npz"`)
- `codebooks_manifest_path` (상대 파일명, 예: `"residual_codebooks_manifest.json"`)

기존 manifest 키는 rename·삭제하지 않는다.

### 로드 시 검증

`load_codebooks`는 다음을 검증해야 한다:

- NPZ 키가 manifest의 `branching_factor`, `depth`, `embedding_dim`, `normalize_residuals`, `level_cluster_counts`와 존재·일관성 모두 맞는다.
- 불일치 시 `ValueError`를 던지며, 메시지에 충돌 필드명과 `compile-sid-index` 재실행 안내를 포함한다.
- 파일 부재는 `FileNotFoundError`로 remediation hint와 함께 던진다(silent downgrade 금지).

## 공개 인터페이스 (Public Interfaces)

### `sid_reco.sid.compiler`

```python
@dataclass(frozen=True, slots=True)
class ItemSID:
    sid_path: tuple[int, ...]
    sid_string: str
    recipe_id: int

@dataclass(frozen=True, slots=True)
class QuerySID:
    sid_path: tuple[int, ...]
    sid_string: str

def train_codebooks(matrix, *, branching_factor=256, depth=3,
                    normalize_residuals=True, max_iter=50,
                    tolerance=1e-6) -> TrainedResidualCodebooks: ...

def build_item_sids(recipe_ids, matrix, *,
                    codebooks: TrainedResidualCodebooks
                    ) -> list[ItemSID]: ...

def build_query_sid(vector, *,
                    codebooks: TrainedResidualCodebooks
                    ) -> QuerySID: ...

def write_codebooks(codebooks: TrainedResidualCodebooks, *,
                    out_dir: Path) -> tuple[Path, Path]:
    """(npz_path, manifest_path) 반환. 둘 다 out_dir 안."""

def load_codebooks(npz_path: Path) -> TrainedResidualCodebooks:
    """NPZ에서 quantizer 로드, 형제 manifest와 교차 검증."""
```

`compile_residual_kmeans`, `assign_trained_residual_kmeans`는 삭제한다.
`train_residual_codebooks`는 `train_codebooks`로 rename한다 (의미는 `TrainedResidualCodebooks` 타입에 이미 드러남).

### `sid_reco.sid.indexing`

```python
@dataclass(frozen=True, slots=True)
class SIDIndexWriteSummary:
    item_count: int
    embedding_dim: int
    compiled_sid_path: Path
    item_to_sid_path: Path
    sid_to_items_path: Path
    id_map_path: Path
    index_path: Path
    manifest_path: Path
    codebooks_path: Path            # 신규
    codebooks_manifest_path: Path   # 신규

def write_sid_index_outputs(
    *,
    embedded: EmbeddedSIDItems,
    codebooks: TrainedResidualCodebooks,
    items: list[ItemSID],
    out_dir: Path,
) -> SIDIndexWriteSummary: ...
```

### `sid_reco.recommendation.semantic_search`

```python
@dataclass(frozen=True, slots=True)
class SemanticCandidate:
    faiss_idx: int
    recipe_id: int
    sid_string: str
    sid_path: tuple[int, ...]       # 신규 — id_map.jsonl에서 보존
    score: float
    serialized_text: str
    taxonomy: Mapping[str, tuple[str, ...]]
    popularity: int
    cooccurrence_with_history: int

@dataclass(frozen=True, slots=True)
class SemanticSearchResult:
    query_text: str
    query_sid: QuerySID            # 신규
    candidates: tuple[SemanticCandidate, ...]
    dropped_candidates: tuple[DroppedCandidate, ...]
    retrieved_count: int
    survivor_count: int
    low_coverage: bool
```

내부 변경: encoder 호출이 `raw_vector`를 생성한다. FAISS는 정규화된 사본(기존 동작)을 사용한다. query-SID 할당에는 `raw_vector`를 그대로 쓴다 — quantizer가 학습 시 본 분포와 동일해야 하기 때문.

### `sid_reco.recommendation.types`

```python
@dataclass(frozen=True, slots=True)
class RecommendationResponse:
    sketch: InterestSketch
    items: tuple[RecommendedItem, ...]
    rerank_summary: str
    confidence_summary: str
    selected_candidate_indices: tuple[int, ...]
    query_sid: QuerySID            # 신규
```

### CLI

`compile-sid-index` 결과 테이블에 한 행 추가:

- `Codebooks path` → `residual_codebooks.npz` 상대 경로

`recommend` 결과 블록의 기존 summary 아래 한 줄 추가:

- `Query SID: <sid_string>  path=<tuple>`

### `apps/demo`

`window.runPipeline(...)` 반환 shape에 다음 추가:

- `conf.items[i].sid_path: number[]` — mock 계층 경로(기존 `buildSid`가 문자열과 path 모두 반환하도록 확장)
- `conf.query_sid: { sid_string: string, sid_path: number[] }` — sketch facets에서 mock으로 도출

`i18n.js` JSON preview와 overview grid copy는 신규 필드가 실제로 노출되는 위치에서만 확장. 그 외 가시 copy 변경 없음.

## 명령 (Commands)

### 기존 검증 명령 (변경 없음)

```bash
uv sync --all-groups
uv run pytest
uv run ruff check .
uv run mypy src
uv run sid-reco doctor
```

### 이 스펙을 위한 타겟 검증

```bash
uv run pytest tests/test_sid_compiler.py tests/test_sid_indexing.py \
              tests/test_cli_compile_sid_index.py tests/test_semantic_search.py \
              tests/test_recommendation_pipeline.py tests/test_cli_recommend.py
uv run ruff check .
uv run mypy src
node apps/demo/tests/pipeline.test.cjs
node apps/demo/tests/i18n.test.cjs
```

### End-to-end smoke (선택, MLX 환경 필요)

```bash
uv run sid-reco compile-sid-index --out-dir data/processed/foodcom/sid_index
uv run sid-reco recommend --query "cozy weeknight vegetarian dinner" --top-k 3
```

## 프로젝트 구조 (Project Structure)

### 수정 파일

```text
src/sid_reco/sid/compiler.py              -> 타입 rename, 새 helper, persistence, query 할당
src/sid_reco/sid/indexing.py              -> 시그니처 변경, codebook artifact write, summary 필드 추가
src/sid_reco/sid/__init__.py              -> export 갱신
src/sid_reco/recommendation/semantic_search.py
                                          -> codebook 로드, query_sid 계산, candidate sid_path 보존
src/sid_reco/recommendation/types.py      -> RecommendationResponse.query_sid
src/sid_reco/recommendation/pipeline.py   -> query_sid를 응답까지 전달
src/sid_reco/recommendation/__init__.py   -> 필요시 QuerySID re-export
src/sid_reco/cli.py                       -> compile-sid-index 호출 정리, recommend 출력 라인 추가
apps/demo/data/pipeline.js                -> buildSid + runPipeline shape 확장
apps/demo/src/app.jsx (최소)              -> query_sid를 결과/JSON preview에 렌더 (신규 필드 노출 위치만)
apps/demo/src/i18n.js                     -> 신규 필드가 나타나는 EN/KR 라벨
tests/test_sid_compiler.py                -> codebook round-trip + query-SID 재현성
tests/test_sid_indexing.py                -> 신규 artifact 파일 + summary 필드 + manifest 키
tests/test_cli_compile_sid_index.py       -> CLI 출력의 codebook path 확인
tests/test_semantic_search.py             -> query_sid + candidate sid_path + missing-codebook 에러
tests/test_recommendation_pipeline.py     -> 응답이 query_sid 포함
tests/test_cli_recommend.py               -> CLI가 query_sid 라인 출력
apps/demo/tests/pipeline.test.cjs         -> mock pipeline shape에 query_sid 포함
apps/demo/tests/i18n.test.cjs             -> 신규 라벨의 EN/KR 동기화
```

### 신규 파일

없음. 모든 변경이 기존 모듈에 들어간다.

### 설계 노트 (`raw/design/notes/`, 한국어)

구현 후 `docs-manager`를 통해 갱신:

- `sid-compilation-indexing.md` — 출력 목록에 codebook artifact 추가
- `phase2-recommendation-runtime.md` — 런타임 계약에 `query_sid` 추가
- `phase2-recommendation-runtime-validation.md` — 신규 테스트 목록 추가

이들은 raw/ 수정이므로 upstream `/graphify` full graph refresh를 트리거한다. 코드 PR의 자동 refresh에 포함되지 않는다.

## 코드 스타일 (Code Style)

저장소의 기존 관례를 계승한다:

- 각 Python 파일 최상단에 `from __future__ import annotations`
- 계약 타입은 `@dataclass(frozen=True, slots=True)`
- I/O는 `Path` 기반. `os.path` 금지.
- CLI는 `typer` + `rich`, 결과는 `rich.table.Table`
- rename/삭제된 타입에 대한 backward-compat shim 금지 — 삭제하고 모든 호출처 갱신
- 누락·무효 artifact에 대한 silent fallback 금지 — remediation 메시지와 함께 raise
- 타입이 이미 드러내는 *무엇*에 대한 주석 금지; 비자명한 *왜*만 한 줄

이 스펙 특화:

- `build_query_sid`는 `normalize_residuals=True`일 때 **raw(L2 정규화 전) encoder output**을 사용해야 한다. `_prepare_level_inputs`가 이미 per-level residual을 정규화하기 때문에 query에서 추가 정규화를 하면 컴파일 시점과 분포가 어긋난다.
- NPZ round-trip은 float32 centroid 기준 비트-동일이어야 한다. 정밀도 손실 금지.

## 테스트 전략 (Testing Strategy)

### 프레임워크

Python은 `pytest` + `ruff` + `mypy`, `apps/demo`는 `node` + 프로젝트 기존 CJS loader.

### 테스트 매트릭스

1. **`tests/test_sid_compiler.py`**
   - 타입: `ItemSID`, `QuerySID`가 예상대로 생성·비교된다.
   - Round-trip: `write_codebooks` → `load_codebooks` 결과가 원본과 구조적으로 동치(centroid `allclose`, 메타데이터 동일).
   - **재현성 (핵심 정합성)**: 임베딩 행렬 `M`, codebooks `C = train_codebooks(M)`, `items = build_item_sids(ids, M, codebooks=C)` 에서 모든 행 `k`에 대해 `build_query_sid(M[k], codebooks=C).sid_path == items[k].sid_path`.
   - 무효 artifact: 잘린 NPZ, `embedding_dim` 불일치 manifest, 형제 manifest 부재 — 각각 충돌 필드명을 명시하는 `ValueError`.

2. **`tests/test_sid_indexing.py`**
   - `write_sid_index_outputs(codebooks=..., items=...)`가 `residual_codebooks.npz`와 `residual_codebooks_manifest.json` 둘 다 쓴다.
   - `SIDIndexWriteSummary`에 두 신규 path 노출.
   - 상위 `manifest.json`이 세 신규 키(상대 경로)를 가진다.
   - 기존 artifact 계약(compiled_sid.jsonl, id_map.jsonl, item_index.faiss 등) 불변 — 기대 스키마와 명시 동등성 검사.

3. **`tests/test_cli_compile_sid_index.py`**
   - CLI 실행 후 두 codebook 파일이 `out_dir`에 존재.
   - CLI `rich` 출력이 상대 파일명과 함께 `Codebooks path` 행을 포함.

4. **`tests/test_semantic_search.py`**
   - query 벡터가 fixture item 임베딩과 동일할 때 `SemanticSearchResult.query_sid`가 그 item의 `sid_path`와 같은 `QuerySID`.
   - `SemanticCandidate.sid_path` tuple이 해당 `faiss_idx`의 `id_map.jsonl` 기록과 일치.
   - codebook artifact 부재 시 FAISS 검색 이전에 clear error.

5. **`tests/test_recommendation_pipeline.py` / `tests/test_cli_recommend.py`**
   - stubbed generator/encoder로 `RecommendationResponse.query_sid`가 end-to-end 채워진다.
   - `recommend` CLI 출력에 `Query SID:` 라인과 예상 `sid_string` 포함.
   - rerank summary, confidence summary, 아이템 rank가 변경 전 baseline과 바이트-동일("동작 변화 없음" 회귀 가드).

6. **`apps/demo/tests/pipeline.test.cjs`**
   - `runPipeline(...)` 반환에 `conf.query_sid.sid_string`, `conf.query_sid.sid_path` 존재.
   - 모든 `conf.items[i]`에 기존 `sid` 문자열 외에 `sid_path: number[]` 존재.

7. **`apps/demo/tests/i18n.test.cjs`**
   - EN, KR 로케일 모두 신규 라벨 키를 가진다 — 로케일 drift 없음.

### 커버리지 태도

모든 신규 공개 함수와 신규 응답 필드는 직접 테스트를 가진다. **재현성 테스트**(항목 1 서브 3)가 단일 최중요 게이트다 — 런타임과 컴파일 경로가 하나의 SID 공간을 공유함을 증명한다.

## 경계 (Boundaries)

### Always

- `TrainedResidualCodebooks`를 `sid_index_dir` 안의 1급 artifact로 저장한다.
- query 시점의 residual 정규화 규칙을 컴파일 시점과 동일하게 사용한다 — 코드 기본값이 아니라 저장된 manifest에서 읽는다.
- `id_map.jsonl`의 `sid_path`를 `SemanticCandidate`에 보존·전달한다.
- codebook artifact 누락·불일치 시 remediation 메시지와 함께 raise.
- manifest의 모든 artifact 경로는 `sid_index_dir` 기준 **상대 파일명**.
- 기존 retrieval, rerank, confidence, grounding 동작을 완전히 동일하게 유지.
- rename/삭제된 타입·함수를 깔끔히 제거 — alias 금지, re-export 금지, stub 주석 금지.

### Ask first

- 기본 출력 디렉터리 변경.
- 스펙 수락 이후 NPZ 키 레이아웃 변경(사용자가 컴파일한 시점부터 artifact 호환성 깨짐).
- `TrainedResidualCodebooks`를 `SIDSpace` 등으로 rename.
- `compile-sid-index` CLI 명령 이름 변경.
- `query_sid`를 retrieval scoring 입력으로 승격(명시 유보).

### Never

- codebook artifact 부재 시 silent downgrade — query-SID를 건너뛰는 "best-effort" 경로 금지.
- 추천 시점에 codebook을 다시 학습.
- query 벡터의 정규화를 컴파일 시점 level-input residual 정규화와 다르게 적용.
- manifest에 절대경로 기재.
- `item_index.faiss`, retrieval `k`, survivor cap, rerank prompt, grounding 로직 수정.
- compat alias(`CompiledSIDItem = ItemSID`) 도입 — rename은 hard cut.
- `apps/demo` mock 파이프라인을 권위 있는 동작으로 취급 — shape 계약 맞춤 용도로만 존재.

## 성공 기준 (Success Criteria)

1. `compile-sid-index`가 `sid_index_dir`에 `residual_codebooks.npz`와 `residual_codebooks_manifest.json`을 쓰고, 상위 `manifest.json`에 상대 경로 항목을 기록한다.
2. `load_codebooks`가 quantizer를 비트-정확하게 round-trip(centroid `allclose`, 메타데이터 동일).
3. 임의의 catalog 임베딩 행 `M[k]`에 대해 `build_query_sid(M[k], codebooks=C)`가 같은 row의 컴파일된 item과 동일한 `sid_path`를 반환. 직접 테스트로 보장.
4. `SemanticSearchResult`가 `query_sid: QuerySID`를 가지고, 각 `SemanticCandidate`가 `sid_path: tuple[int, ...]`를 가진다.
5. `RecommendationResponse`가 `query_sid: QuerySID`를 가지고, `recommend` CLI가 출력한다.
6. 누락·불일치 codebook artifact는 remediation 텍스트가 포함된 지정 에러를 raise. silent fallback 없음.
7. 동일 stubbed LLM/encoder fixture에서 rerank summary, confidence summary, ranked `recipe_id`, grounded payload가 변경 전 baseline과 동일.
8. `apps/demo/data/pipeline.js` 반환 shape에 `query_sid`와 per-candidate `sid_path`가 포함되고 `i18n.js` 두 로케일이 동기.
9. `src/`, `tests/` 어디에도 `CompiledSIDItem`, `CompiledSIDItems`, `compile_residual_kmeans`, `assign_trained_residual_kmeans`, `train_residual_codebooks`, `write_trained_codebooks`, `load_trained_codebooks`, `assign_items_to_sid`, `assign_query_embedding_to_sid`가 import되지 않는다.
10. `uv run pytest`, `uv run ruff check .`, `uv run mypy src`가 모두 통과하고 `apps/demo/tests/*.cjs` 통과.

## 확정 결정 (Resolved Decisions)

1. **NPZ 키 인덱싱** — 1-based (`level_1_*` ... `level_N_*`). [src/sid_reco/sid/compiler.py:121](src/sid_reco/sid/compiler.py:121)의 기존 `ResidualKMeansLevel.level` 관례와 일치.
2. **할당 타입 구조** — `ItemSID`·`QuerySID` 두 구체 dataclass만 둔다. base dataclass 없음. 공통 필드 `sid_path`·`sid_string`의 2필드 중복(총 4줄)은 상속 인프라보다 저렴하고, 실제 코드에 두 타입을 공통으로 다루는 호출자가 없다.
3. **함수 네이밍** — `_trained_`·`_residual_` 수식어는 `TrainedResidualCodebooks` 타입 이름이 이미 전달하므로 함수에서 제거. `assign_*_to_sid`의 `assign_` 접두사는 `build_*_sids` / `build_*_sid` 동사로 대체. 결과: `train_codebooks`, `write_codebooks`, `load_codebooks`, `build_item_sids`, `build_query_sid`.
4. **`apps/demo` mock `query_sid`** — `buildSid` 패턴에 `QSID::` 접두사를 붙여 재사용하며 `sketch.positive_facets` 슬롯(cuisine → dish_type → flavor_profile)을 입력으로 한다. 슬롯 부재 시 `"any"`로 fallback. mock 전용.
5. **codebook artifact 에러 타입** — 파일 부재는 built-in `FileNotFoundError`, 스키마·shape 불일치는 `ValueError`. 기존 `_load_id_map` 관례와 일치. silent downgrade 방지를 위해 메시지에 재실행 명령 `uv run sid-reco compile-sid-index --out-dir <dir>` 반드시 포함.
6. **raw/design/notes** — 이 PR에서 제외. 후속 `docs-manager` pass에서 `sid-compilation-indexing.md`, `phase2-recommendation-runtime.md`, `phase2-recommendation-runtime-validation.md`를 갱신하고 upstream `/graphify` full graph refresh를 실행한다.

## 리뷰용 구현 노트 (Implementation Notes for Review)

- 이 스펙은 이전에 `SPEC.md`를 채우던 Phase 2 end-to-end 스펙을 대체한다. Phase 2 내용은 `src/sid_reco/recommendation/` 하위 실구현 코드로 landed 되었고 의도는 `raw/design/notes/phase2-recommendation-runtime.md`와 AGENTS.md 모듈 테이블에 남는다.
- 단일 묶음 PR. 타입·네이밍 정리와 런타임 재현이 함께 간다 — 런타임 기능이 `QuerySID`·`build_query_sid`를 도입하고, 정리가 `ItemSID`·`build_item_sids`의 명명·책임 경계를 확정하기 때문이다.
- `raw/design/notes/` 갱신은 코드 PR에서 의도적으로 분리되어 후속 `docs-manager` pass로 넘긴다. 이는 upstream `/graphify` full graph refresh가 안정된 코드 트리 위에서 실행되도록 하기 위함이다.
- 이 스펙이 리뷰·수락되기 전에는 구현에 착수하지 않는다.
