# Graphify 평가 런북

## 목적

이 문서는 `/graphify` migration 이후 Graphify를 **그래프 품질 / 설명 품질 / 코딩 어시스턴트 효용**
세 축으로 반복 평가하기 위한 기본 절차를 정리한다.

## 평가 기준선

- 1차 기준선 worktree:
  - `feature/graphify-upstream-entrypoint`
  - `/Users/skiiwoo/PERSONAL/Training-Free-SID-Reco-graphify-upstream-entrypoint`
- 기본 기준은 committed `graphify-out/GRAPH_REPORT.md`와 `graphify-out/graph.json`이다.
- `/graphify .`의 기본 입력 경계는 루트 `.graphifyignore`로 해석한다.

## 평가 자산

- graph expectation:
  - `tests/fixtures/graphify_eval/graph_expectation_document_context.json`
- explanation question bank:
  - `tests/fixtures/graphify_eval/question_bank.json`
- assistant A/B task set:
  - `tests/fixtures/graphify_eval/assistant_task_set.json`

## 평가 순서

1. 필요한 경우 upstream `/graphify`로 그래프를 갱신한다.
   - 기본 `/graphify .` 입력 경계는 `.graphifyignore`가 정한다.
   - 특정 subfolder나 corpus를 보려면 path를 명시한다.
2. 그래프 품질을 측정한다.
3. explanation question bank로 what / why / path / explain 답변을 채점한다.
4. 동일 task set으로 baseline vs graph A/B 결과를 기록한다.
5. 세 결과를 scorecard로 합친다.

## 예시 명령

### 1. graph quality

```bash
uv run python scripts/graphify_eval.py graph-quality \
  --graph tests/fixtures/graphify/document_context_graph.json \
  --expectation tests/fixtures/graphify_eval/graph_expectation_document_context.json
```

### 2. explanation quality

```bash
uv run python scripts/graphify_eval.py explanations \
  --question-bank tests/fixtures/graphify_eval/question_bank.json \
  --answers tests/fixtures/graphify_eval/answers_passing.json
```

### 3. assistant utility

```bash
uv run python scripts/graphify_eval.py assistant-utility \
  --benchmark tests/fixtures/graphify_eval/assistant_task_set.json \
  --runs tests/fixtures/graphify_eval/assistant_runs_passing.json
```

### 4. 통합 scorecard

```bash
uv run python scripts/graphify_eval.py scorecard \
  --graph tests/fixtures/graphify/document_context_graph.json \
  --expectation tests/fixtures/graphify_eval/graph_expectation_document_context.json \
  --question-bank tests/fixtures/graphify_eval/question_bank.json \
  --answers tests/fixtures/graphify_eval/answers_passing.json \
  --benchmark tests/fixtures/graphify_eval/assistant_task_set.json \
  --runs tests/fixtures/graphify_eval/assistant_runs_passing.json
```

## 해석 원칙

1. **그래프 품질**
   - required node / source / relation이 빠지면 fail로 본다.
   - code-only 그래프는 document-context expectation을 만족하면 안 된다.
2. **설명 품질**
   - why 답변은 `raw/design/**` 근거를 반드시 들어야 한다.
   - 근거가 없으면 추정하지 말고 abstain하도록 설계한다.
3. **assistant utility**
   - graph variant는 baseline보다 정확도가 낮아지면 안 된다.
   - 정확도, 턴 수, 소요 시간 중 최소 하나는 개선되어야 한다.
   - 잘못 건드린 파일 수는 baseline보다 늘어나면 안 된다.

## 실제 저장소 평가 시 주의점

1. fixture 평가는 deterministic baseline이다.
2. 실제 저장소 평가에서는 `GRAPH_REPORT.md`, `graph.json`, `.graphifyignore`를 함께 읽고 같은
   question bank와 A/B task set을 재사용한다.
3. docs/design 질문은 실제 graph에 해당 source context가 들어왔는지 확인한 뒤 합격 판단을 내려야 한다.
