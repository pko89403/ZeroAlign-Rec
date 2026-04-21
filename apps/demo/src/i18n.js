/* Translation + preset tables for ZeroAlign-Rec demo.
 * Consumed by src/components.jsx; loaded as a plain <script> before Babel/React code. */

const EN = {
  lang: "en",
  docTitle: "ZeroAlign-Rec — Recommendation Demo",
  otherLang: { lang: "kr", label: "KR" },
  pageTitle: { a: "Training-free", b: "SID", c: "recommendation" },
  pageSub: "FOOD.COM · PHASE 1 ARTIFACTS + 4-MODULE ONLINE PIPELINE · MLX LOCAL",

  sb: {
    brandSub: "Phase 2 · Training-free",
    presets: "Preset scenarios",
    query: "Natural-language query",
    queryPh: "e.g. hearty but not heavy comfort food…",
    history: "Liked / Disliked items",
    filters: "Hard filters (CPU)",
    topK: "Delivery top-k",
    topKSub: "items returned",
    runIdle: "Run recommendation pipeline",
    runBusy: "Running pipeline…",
  },

  tabs: [
    { id: "overview", num: "OVERVIEW", label: "Summary",               sub: "4-stage pipeline status" },
    { id: "final",    num: "DELIVERY", label: "Final Recommendations", sub: "grounded results" },
    { id: "m21",      num: "2.1",      label: "Interest Sketch",       sub: "taxonomy-constrained" },
    { id: "m22",      num: "2.2",      label: "Semantic Search",       sub: "FAISS + hard filter" },
    { id: "m23",      num: "2.3",      label: "Zero-Shot Rerank",      sub: "5 order-perturbed passes" },
    { id: "m24",      num: "2.4",      label: "MSCP Confidence",       sub: "CPU vote aggregation" },
    { id: "json",     num: "API",      label: "Response JSON",         sub: "structured contract" },
  ],

  pipeline: [
    { num: "2.1", title: "Interest Sketch",  sub: "Taxonomy-constrained",       tKey: "simSketch" },
    { num: "2.2", title: "Semantic Search",  sub: "FAISS cosine + hard filter", tKey: "simRetrieval" },
    { num: "2.3", title: "Zero-Shot Rerank", sub: "5 order-perturbed passes",   tKey: "simRerank" },
    { num: "2.4", title: "MSCP + Grounding", sub: "CPU vote aggregation",       tKey: "simConfidence" },
  ],
  runtimeTag: "MLX local",
  stageDone: ms => `${ms}ms`,
  stageActive: "running…",
  stageQueued: "queued",

  metrics: {
    totalLatency: "total latency",
    retrieved: "retrieved",
    droppedByHF: "dropped by HF",
    rerankPasses: "rerank passes",
    avgMscp: "avg MSCP",
    ood: "OOD",
  },

  p21: {
    title: "Interest Sketch",
    sub: "taxonomy-guarded · vocabulary = master dictionary",
    kvpSummary: "query summary",
    kvpAmbiguity: "ambiguity",
    positive: "Positive facets",
    negative: "Negative facets & hard filters",
    emptyPos: "(none extracted)",
    emptyNegHF: "(none)",
  },

  p22: {
    title: "Semantic Search + CPU Hard Filter",
    sub: "FAISS IndexFlatIP · cosine · over-sampled Top-100 → Top-30",
    surviving: "Surviving candidates",
    dropped: "Dropped by hard filters",
    noDrop: "no items dropped",
    candMeta: c => `pop ${c.popularity.toFixed(2)} · cooc ${c.cooccurrence} · ${c.cuisine}`,
  },

  p23: {
    title: "Zero-Shot Rerank · 5 order-perturbed passes",
    sub: "schema-constrained output · 1 dynamic few-shot · candidate-index only",
    pass: "pass",
    footLeft: "LLM → ",
    footModel: "Qwen3.5-9B-OptiQ-4bit",
    footRight: " · constrained to JSON schema · max_tokens=1024 · prefix-cache reuse",
  },

  p24: {
    title: "MSCP Confidence · CPU vote aggregation + elastic grounding",
    sub: "OOD = 0% · id_map.jsonl + sid_to_items.json",
    voteHeader: "DCG-weighted vote distribution across passes",
    mscpLabel: "MSCP",
    band: { HIGH: "HIGH", MEDIUM: "MEDIUM", LOW: "LOW" },
  },

  final: {
    title: "Final grounded recommendations",
    sub: "canonical metadata + short reasoning",
    bandPrefix: "",
    meta: r => `${r.cuisine} · ${r.time} min · ${r.calories} cal`,
    bootstrap: n => `bootstrap ${n}/5`,
  },

  overview: {
    m21Title: "Interest Sketch",
    m21Body1: n => `${n} positive facets`,
    m21Body2: n => `${n} hard filters`,
    m22Title: "Semantic Search",
    m22Body1: n => `${n} surviving`,
    m22Body2: n => `${n} dropped`,
    m23Title: "Zero-Shot Rerank",
    m23Body1: n => `${n} passes`,
    m23Body2: "JSON-schema constrained",
    m24Title: "MSCP Confidence",
    m24Body1: m => `avg MSCP ${m}`,
    m24Body2: "OOD 0%",
    cta: "View details →",
  },

  json: {
    title: "RecommendationResponse",
    sub: "structured contract · library + CLI",
    rerankSummary: topK => `5 order-perturbed passes aggregated with DCG weighting; top-${topK} stabilized`,
    confAllHigh: "all HIGH — strong semantic + popularity agreement",
    confMixed: "mixed bands — see individual MSCP",
  },

  idleText: ["Pipeline idle. Click ", "Run recommendation pipeline", " on the left."],

  dietLabel: d => d,

  a11y: {
    likeBtn:       title => `Like ${title}`,
    dislikeBtn:    title => `Dislike ${title}`,
    langSwitchTo:  "Switch to Korean",
    jsonRegion:    "Response JSON payload",
  },

  presets: [
    { id: "cozy-veg",
      label: "Cozy vegetarian weeknight",
      sub: "Hearty but not heavy",
      query: "I want hearty but not too heavy comfort food for a weeknight. Vegetarian.",
      liked: [110, 111], disliked: [], filters: { dietary_style: ["vegetarian"] }, topK: 3 },
    { id: "spicy-quick",
      label: "Spicy & quick, gluten-free",
      sub: "Heat in under 20 min",
      query: "Something spicy that I can make fast. No gluten.",
      liked: [117, 105], disliked: [104], filters: { dietary_style: ["gluten-free"] }, topK: 3 },
    { id: "weekend-project",
      label: "Weekend project, rich flavors",
      sub: "Worth the time",
      query: "I have time this weekend and want something rich and impressive.",
      liked: [106, 120], disliked: [], filters: {}, topK: 3 },
    { id: "fresh-light",
      label: "Fresh, light lunch",
      sub: "Crisp and clean",
      query: "Light and fresh lunch. Nothing heavy.",
      liked: [113, 119], disliked: [125], filters: {}, topK: 3 },
  ],
};

const KR_DIETARY_LABELS = {
  "vegetarian": "채식",
  "vegan": "비건",
  "gluten-free": "글루텐프리",
  "pescatarian": "페스코",
  "omnivore": "잡식",
};
const KR_BAND = { HIGH: "높음", MEDIUM: "보통", LOW: "낮음" };

const KR = {
  lang: "ko",
  docTitle: "ZeroAlign-Rec — 레시피 추천 데모",
  otherLang: { lang: "en", label: "EN" },
  pageTitle: { a: "학습 없는", b: "SID", c: "레시피 추천" },
  pageSub: "FOOD.COM · PHASE 1 아티팩트 + 4모듈 온라인 파이프라인 · MLX 로컬 실행",

  sb: {
    brandSub: "Phase 2 · 학습 없는 추천",
    presets: "시나리오 프리셋",
    query: "자연어 질의",
    queryPh: "예: 담백하면서 속이 편한 평일 저녁…",
    history: "좋아요 / 싫어요 이력",
    filters: "하드 필터 (CPU)",
    topK: "전달 top-k",
    topKSub: "반환 아이템 수",
    runIdle: "추천 파이프라인 실행",
    runBusy: "파이프라인 실행 중…",
  },

  tabs: [
    { id: "overview", num: "개요",  label: "전체 요약",      sub: "4단계 파이프라인 상태" },
    { id: "final",    num: "전달",  label: "최종 추천",      sub: "grounded 결과" },
    { id: "m21",      num: "2.1",  label: "관심 스케치",    sub: "택소노미 기반 추출" },
    { id: "m22",      num: "2.2",  label: "시맨틱 검색",    sub: "FAISS + 하드 필터" },
    { id: "m23",      num: "2.3",  label: "제로샷 리랭킹",   sub: "5회 순서 교란" },
    { id: "m24",      num: "2.4",  label: "MSCP 신뢰도",    sub: "CPU 투표 집계" },
    { id: "json",     num: "API",  label: "응답 JSON",      sub: "구조화된 계약" },
  ],

  pipeline: [
    { num: "2.1", title: "관심 스케치",           sub: "택소노미 기반 추출",        tKey: "simSketch" },
    { num: "2.2", title: "시맨틱 검색",           sub: "FAISS 코사인 + 하드 필터",  tKey: "simRetrieval" },
    { num: "2.3", title: "제로샷 리랭킹",          sub: "5회 순서 교란 통과",        tKey: "simRerank" },
    { num: "2.4", title: "MSCP 신뢰도 + 그라운딩", sub: "CPU 투표 집계",            tKey: "simConfidence" },
  ],
  runtimeTag: "MLX 로컬",
  stageDone: ms => `${ms}ms`,
  stageActive: "실행 중…",
  stageQueued: "대기",

  metrics: {
    totalLatency: "전체 지연시간",
    retrieved: "검색 결과",
    droppedByHF: "하드 필터 제외",
    rerankPasses: "리랭킹 패스",
    avgMscp: "평균 MSCP",
    ood: "OOD",
  },

  p21: {
    title: "관심 스케치",
    sub: "택소노미 가드 · 마스터 사전 어휘만 사용",
    kvpSummary: "질의 요약",
    kvpAmbiguity: "모호성",
    positive: "긍정 패싯",
    negative: "부정 패싯 & 하드 필터",
    emptyPos: "(추출되지 않음)",
    emptyNegHF: "(없음)",
  },

  p22: {
    title: "시맨틱 검색 + CPU 하드 필터",
    sub: "FAISS IndexFlatIP · 코사인 · 과표집 Top-100 → Top-30",
    surviving: "생존 후보",
    dropped: "하드 필터로 제외",
    noDrop: "제외된 아이템 없음",
    candMeta: c => `인기도 ${c.popularity.toFixed(2)} · 공출현 ${c.cooccurrence} · ${c.cuisine}`,
  },

  p23: {
    title: "제로샷 리랭킹 · 5회 순서 교란 통과",
    sub: "스키마 제약 출력 · 동적 few-shot 1건 · 후보 인덱스만 사용",
    pass: "패스",
    footLeft: "LLM → ",
    footModel: "Qwen3.5-9B-OptiQ-4bit",
    footRight: " · JSON 스키마 제약 · max_tokens=1024 · 프리픽스 캐시 재사용",
  },

  p24: {
    title: "MSCP 신뢰도 · CPU 투표 집계 + 탄성 그라운딩",
    sub: "OOD = 0% · id_map.jsonl + sid_to_items.json",
    voteHeader: "DCG 가중 투표 분포 · 전체 패스 기준",
    mscpLabel: "MSCP",
    band: KR_BAND,
  },

  final: {
    title: "최종 grounded 추천",
    sub: "정규화 메타데이터 + 짧은 추천 이유",
    bandPrefix: "신뢰도 ",
    meta: r => `${r.cuisine} · ${r.time}분 · ${r.calories} kcal`,
    bootstrap: n => `부트스트랩 ${n}/5`,
  },

  overview: {
    m21Title: "관심 스케치",
    m21Body1: n => `긍정 패싯 ${n}개`,
    m21Body2: n => `하드 필터 ${n}개`,
    m22Title: "시맨틱 검색",
    m22Body1: n => `생존 ${n}개`,
    m22Body2: n => `제외 ${n}개`,
    m23Title: "제로샷 리랭킹",
    m23Body1: n => `${n}회 패스`,
    m23Body2: "JSON 스키마 제약",
    m24Title: "MSCP 신뢰도",
    m24Body1: m => `평균 MSCP ${m}`,
    m24Body2: "OOD 0%",
    cta: "자세히 →",
  },

  json: {
    title: "RecommendationResponse",
    sub: "구조화된 계약 · 라이브러리 + CLI",
    rerankSummary: topK => `5회 순서 교란 패스 · DCG 가중 집계 · top-${topK} 안정화`,
    confAllHigh: "모두 HIGH — 시맨틱 + 인기도 강한 합치",
    confMixed: "혼합 밴드 — 개별 MSCP 참조",
  },

  idleText: ["파이프라인 대기 중. 좌측의 ", "추천 파이프라인 실행", " 버튼을 눌러주세요."],

  dietLabel: d => KR_DIETARY_LABELS[d] || d,

  a11y: {
    likeBtn:       title => `${title} 좋아요`,
    dislikeBtn:    title => `${title} 싫어요`,
    langSwitchTo:  "Switch to English",
    jsonRegion:    "응답 JSON 페이로드",
  },

  presets: [
    { id: "cozy-veg",
      label: "평일 저녁 · 채식 위주",
      sub: "담백하고 속이 편한 한 끼",
      query: "평일 저녁에 부담 없이 먹을 수 있는 든든한 채식 요리가 먹고 싶어요.",
      liked: [110, 111], disliked: [], filters: { dietary_style: ["vegetarian"] }, topK: 3 },
    { id: "spicy-quick",
      label: "빠르게 · 매콤하게 · 글루텐프리",
      sub: "20분 안에 끝나는 매운맛",
      query: "빨리 만들 수 있는 매콤한 요리요. 글루텐은 안 먹어요.",
      liked: [117, 105], disliked: [104], filters: { dietary_style: ["gluten-free"] }, topK: 3 },
    { id: "weekend-project",
      label: "주말 · 진하고 임팩트 있게",
      sub: "시간을 들일 만한 요리",
      query: "이번 주말에 시간을 들여서 만들 수 있는, 깊고 진한 풍미의 요리를 찾고 있어요.",
      liked: [106, 120], disliked: [], filters: {}, topK: 3 },
    { id: "fresh-light",
      label: "산뜻한 점심",
      sub: "가볍고 신선한 한 끼",
      query: "가볍고 산뜻한 점심이요. 무거운 건 빼주세요.",
      liked: [113, 119], disliked: [125], filters: {}, topK: 3 },
  ],
};

window.I18N = { en: EN, kr: KR };
