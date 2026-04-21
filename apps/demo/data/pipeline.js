// ZeroAlign-Rec online pipeline — 4 modules.
// Depends on: window.TAXONOMY (data/taxonomy.js), window.RECIPES (data/recipes.js)

// ---------- Module 2.1: Interest-sketch extraction ----------

// Keyword → taxonomy mapping. Order matters only for readability.
const KEYWORD_MAP = [
  { kws: ["spicy","spice","hot","heat"],             facet: "flavor_profile", value: "spicy" },
  { kws: ["creamy","rich"],                          facet: "flavor_profile", value: "rich" },
  { kws: ["fresh","light"],                          facet: "flavor_profile", value: "fresh" },
  { kws: ["umami","savory"],                         facet: "flavor_profile", value: "umami" },
  { kws: ["sweet","dessert"],                        facet: "flavor_profile", value: "sweet" },
  { kws: ["herb","herby"],                           facet: "flavor_profile", value: "herbaceous" },
  { kws: ["hearty","comfort","cozy"],                facet: "flavor_profile", value: "umami" },
  { kws: ["not too heavy","not heavy","light"],      facet: "effort",         value: "weeknight" },
  { kws: ["weeknight","weekday","fast","quick"],     facet: "effort",         value: "quick" },
  { kws: ["weekend","project","impressive"],         facet: "effort",         value: "weekend-project" },
  { kws: ["vegetarian"],                             facet: "dietary_style",  value: "vegetarian" },
  { kws: ["vegan"],                                  facet: "dietary_style",  value: "vegan" },
  { kws: ["no gluten","gluten-free","gluten free"],  facet: "dietary_style",  value: "gluten-free" },
  { kws: ["lunch"],                                  facet: "meal_type",      value: "lunch" },
  { kws: ["dinner"],                                 facet: "meal_type",      value: "dinner" },
  { kws: ["breakfast"],                              facet: "meal_type",      value: "breakfast" },
  { kws: ["soup"],                                   facet: "dish_type",      value: "soup" },
  { kws: ["noodle","noodles"],                       facet: "dish_type",      value: "noodles" },
  { kws: ["bowl"],                                   facet: "dish_type",      value: "bowl" },
];

const recipeById = id => window.RECIPES.find(r => r.id === id);

const pushUnique = (obj, key, value) => {
  if (!obj[key]) obj[key] = [];
  if (!obj[key].includes(value)) obj[key].push(value);
};

window.buildSketch = function (query, liked = [], disliked = [], hardFilters = {}) {
  const q = (query || "").toLowerCase();
  const sketch = {
    summary: query || "(no free-text query)",
    positive_facets: {},
    negative_facets: {},
    hard_filters: { ...hardFilters },
    ambiguity_notes: [],
  };

  // Free-text → facets
  for (const m of KEYWORD_MAP) {
    if (m.kws.some(k => q.includes(k))) pushUnique(sketch.positive_facets, m.facet, m.value);
  }

  // Liked items → positive facets
  for (const id of liked) {
    const r = recipeById(id); if (!r) continue;
    pushUnique(sketch.positive_facets, "cuisine",   r.cuisine);
    pushUnique(sketch.positive_facets, "dish_type", r.dish);
    for (const f of r.flavors) pushUnique(sketch.positive_facets, "flavor_profile", f);
  }

  // Disliked items → negative flavor facets
  for (const id of disliked) {
    const r = recipeById(id); if (!r) continue;
    for (const f of r.flavors) pushUnique(sketch.negative_facets, "flavor_profile", f);
  }

  // Ambiguity notes
  if (!query || query.length < 10) {
    sketch.ambiguity_notes.push("sparse query — relying on liked items");
  }
  if (q.includes("not too heavy") && q.includes("hearty")) {
    sketch.ambiguity_notes.push("'hearty but not heavy' — ambiguous richness target");
  }

  return sketch;
};


// ---------- Module 2.2: Semantic search + CPU hard filter ----------

// How each facet is matched against a recipe field.
const FACET_MATCHERS = {
  cuisine:        (r, v) => r.cuisine === v,
  dish_type:      (r, v) => r.dish === v,
  meal_type:      (r, v) => r.meal === v,
  effort:         (r, v) => r.effort === v,
  flavor_profile: (r, v) => r.flavors.includes(v),
  cooking_method: (r, v) => r.method === v,
  dietary_style:  (r, v) => r.dietary.includes(v),
};

const FACET_WEIGHTS = {
  flavor_profile: 0.30,
  cuisine:        0.25,
  dish_type:      0.20,
  effort:         0.15,
  meal_type:      0.10,
};
const DEFAULT_FACET_WEIGHT = 0.08;
const NEGATIVE_PENALTY = 0.10;

// Deterministic pseudo-random jitter so scores feel vector-y but stay reproducible.
const noiseFor = id => ((id * 9301 + 49297) % 233280) / 233280 * 0.04;

// Per-recipe score against the sketch.
function scoreRecipe(recipe, sketch) {
  let score = 0;
  const matched = [];

  for (const [facet, values] of Object.entries(sketch.positive_facets)) {
    const w = FACET_WEIGHTS[facet] ?? DEFAULT_FACET_WEIGHT;
    const match = FACET_MATCHERS[facet];
    if (!match) continue;
    for (const v of values) {
      if (match(recipe, v)) { score += w; matched.push(`${facet}=${v}`); }
    }
  }

  for (const [facet, values] of Object.entries(sketch.negative_facets || {})) {
    const match = FACET_MATCHERS[facet];
    if (!match) continue;
    for (const v of values) if (match(recipe, v)) score -= NEGATIVE_PENALTY;
  }

  return { ...recipe, score: Math.max(0, score + noiseFor(recipe.id)), matched };
}

// Each entry returns either null (keep) or a reason string (drop).
const HARD_FILTERS = {
  dietary_style: (r, values) => {
    for (const d of values) if (!r.dietary.includes(d)) return `missing dietary:${d}`;
    return null;
  },
  cuisine:  (r, values) => values.includes(r.cuisine) ? null : `cuisine not in ${values.join(",")}`,
  max_time: (r, limit)  => r.time > limit ? `time ${r.time}>${limit}` : null,
};

function applyHardFilters(candidates, hardFilters) {
  const survivors = [];
  const dropped   = [];
  for (const r of candidates) {
    let reason = null;
    for (const [key, spec] of Object.entries(hardFilters)) {
      const fn = HARD_FILTERS[key];
      if (!fn) continue;
      reason = fn(r, spec);
      if (reason) break;
    }
    if (reason) dropped.push({ id: r.id, title: r.title, reason });
    else        survivors.push(r);
  }
  return { survivors, dropped };
}

// Approximate collaborative-filter features derived from liked history.
function attachCfFeatures(candidates, likedIds) {
  const likedRecipes = likedIds.map(recipeById).filter(Boolean);
  for (const r of candidates) {
    r.popularity  = r.pop;
    r.cooccurrence = likedRecipes.filter(l => l.cuisine === r.cuisine || l.dish === r.dish).length;
  }
}

window.semanticSearch = function (sketch, { topN = 100, topK = 30 } = {}) {
  const top100 = window.RECIPES
    .map(r => scoreRecipe(r, sketch))
    .sort((a, b) => b.score - a.score)
    .slice(0, topN);

  const { survivors, dropped } = applyHardFilters(top100, sketch.hard_filters || {});
  const top30 = survivors.slice(0, topK);
  attachCfFeatures(top30, sketch._liked || []);

  return { top100, top30, dropped };
};


// ---------- Module 2.3: Zero-shot rerank with K order-perturbed passes ----------

const RERANK_COOC_WEIGHT = 0.20;
const RERANK_POP_WEIGHT  = 0.15;

function buildRationale(candidate) {
  const keyMatches = candidate.matched.slice(0, 2);
  const popTag =
    candidate.popularity > 0.75 ? "Strong popularity signal." :
    candidate.popularity < 0.60 ? "Niche but aligned." :
                                  "Balanced fit.";
  return `Matches ${keyMatches.join(", ") || "taxonomy anchors"}. ${popTag}`;
}

window.zeroShotRerank = function (candidates, _sketch, { passes = 5 } = {}) {
  const basis = candidates.map((c, idx) => ({
    idx, id: c.id,
    base: c.score * (1 + RERANK_COOC_WEIGHT * c.cooccurrence) * (1 + RERANK_POP_WEIGHT * c.popularity),
  }));

  // Each pass jitters basis scores with a pass-specific seed.
  const passResults = [];
  for (let p = 0; p < passes; p++) {
    const seed = (p + 1) * 1.37;
    const perturbed = basis
      .map(b => ({ ...b, jittered: b.base + Math.sin(b.idx * seed) * 0.04 + Math.cos(b.id * seed) * 0.02 }))
      .sort((a, b) => b.jittered - a.jittered);
    passResults.push(perturbed.slice(0, 10).map(x => x.idx + 1)); // 1-indexed
  }

  // Build rationales once — shared across all passes.
  const rationales  = {};
  const matchedPrefs = {};
  candidates.forEach((c, idx) => {
    rationales[idx + 1]   = buildRationale(c);
    matchedPrefs[idx + 1] = c.matched.slice(0, 3);
  });

  return { passes: passResults, rationales, matchedPrefs };
};


// ---------- Module 2.4: MSCP confidence + grounding ----------

// DCG-style weight: rank 0 gets 1.0, rank 1 gets 0.63, etc.
const dcgWeight = pos => 1 / Math.log2(pos + 2);

const mscpBand = mscp => mscp >= 0.8 ? "HIGH" : mscp >= 0.5 ? "MEDIUM" : "LOW";

function buildSid(recipe) {
  const flavor = recipe.flavors?.[0] ?? "default";
  return `SID::${recipe.cuisine.toLowerCase()}::${recipe.dish}::${flavor}::${recipe.id}`;
}

window.computeConfidenceAndGround = function (candidates, rerankResult, topK = 3) {
  // 1. Aggregate DCG-weighted votes across passes.
  const voteMap = {};
  for (const pass of rerankResult.passes) {
    pass.forEach((idx, pos) => {
      voteMap[idx] = (voteMap[idx] || 0) + dcgWeight(pos);
    });
  }
  const allVotes = Object.entries(voteMap)
    .map(([idx, votes]) => ({ idx: +idx, votes }))
    .sort((a, b) => b.votes - a.votes);

  // 2. For the top-k winners, compute MSCP = fraction of passes in which they
  //    appeared inside the top-k slots.
  const totalPasses = rerankResult.passes.length;
  const items = allVotes
    .slice(0, topK)
    .map((entry, rank) => {
      const recipe = candidates[entry.idx - 1];
      if (!recipe) return null;

      const appearTopK = rerankResult.passes.filter(p => p.slice(0, topK).includes(entry.idx)).length;
      const bootstrap  = rerankResult.passes.filter(p => p.includes(entry.idx)).length;
      const mscp       = appearTopK / totalPasses;

      return {
        rank:               rank + 1,
        idx:                entry.idx,
        recipe,
        rationale:          rerankResult.rationales[entry.idx],
        matched_preferences: rerankResult.matchedPrefs[entry.idx],
        mscp,
        confidence_band:    mscpBand(mscp),
        bootstrap_support:  bootstrap,
        mapping_mode:       "direct (id_map.jsonl)",
        sid:                buildSid(recipe),
      };
    })
    .filter(Boolean);

  return { items, allVotes };
};


// ---------- End-to-end pipeline ----------

// Simulated wall-clock latencies so the UI can animate stage transitions.
function simulatedTimings() {
  const rand = n => Math.round(Math.random() * n);
  return {
    simSketch:     180 + rand(40),
    simRetrieval:   35 + rand(10),
    simRerank:     720 + rand(120),
    simConfidence:   8 + rand(4),
  };
}

window.runPipeline = function ({ query, liked, disliked, hardFilters, topK = 3 }) {
  const t0 = performance.now();
  const sketch = window.buildSketch(query, liked, disliked, hardFilters);
  sketch._liked = liked; // passed through to retrieval for co-occurrence features
  const t1 = performance.now();

  const search = window.semanticSearch(sketch);
  const t2 = performance.now();

  const rerank = window.zeroShotRerank(search.top30, sketch, { passes: 5 });
  const t3 = performance.now();

  const conf = window.computeConfidenceAndGround(search.top30, rerank, topK);
  const t4 = performance.now();

  return {
    sketch, search, rerank, conf,
    timings: {
      sketch:     t1 - t0,
      retrieval:  t2 - t1,
      rerank:     t3 - t2,
      confidence: t4 - t3,
      total:      t4 - t0,
      ...simulatedTimings(),
    },
  };
};
