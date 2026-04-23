const { test } = require("node:test");
const assert = require("node:assert/strict");
const { loadDemoGlobals } = require("./_loader.cjs");

const W = loadDemoGlobals();

// ---------- 2.1 Interest Sketch ----------

test("buildSketch: empty query yields 'sparse query' ambiguity note", () => {
  const s = W.buildSketch("", [], [], {});
  assert.ok(s.ambiguity_notes.some(n => n.includes("sparse query")));
});

test("buildSketch: 'spicy ... no gluten' produces matching positive facets", () => {
  const s = W.buildSketch("Something spicy that I can make fast. No gluten.", [], [], {});
  assert.ok(s.positive_facets.flavor_profile?.includes("spicy"));
  assert.ok(s.positive_facets.dietary_style?.includes("gluten-free"));
  assert.ok(s.positive_facets.effort?.includes("quick"));
});

test("buildSketch: liked items pull cuisine/dish/flavors into positive facets", () => {
  // 110 = Wild Mushroom Risotto (Italian, rice-dish, [umami, creamy])
  const s = W.buildSketch("", [110], [], {});
  assert.ok(s.positive_facets.cuisine?.includes("Italian"));
  assert.ok(s.positive_facets.dish_type?.includes("rice-dish"));
  assert.ok(s.positive_facets.flavor_profile?.includes("umami"));
});

test("buildSketch: disliked items pull flavors into negative facets", () => {
  // 104 = Lemon Ricotta Pancakes (flavors: [sweet, tangy])
  const s = W.buildSketch("", [], [104], {});
  assert.ok(s.negative_facets.flavor_profile?.includes("sweet"));
});

test("buildSketch: hard filters are preserved verbatim", () => {
  const hf = { dietary_style: ["vegan"], max_time: 30 };
  const s = W.buildSketch("", [], [], hf);
  // JSON-normalize: pipeline.js runs in a vm context with a separate
  // Object.prototype, so cross-realm deepStrictEqual would otherwise fail
  // on prototype identity even when the structure matches.
  assert.deepEqual(JSON.parse(JSON.stringify(s.hard_filters)), hf);
});

test("buildSketch: undefined liked/disliked/hardFilters do not throw (default args)", () => {
  // Regression guard for review fix #2 — signature is now defaulted.
  assert.doesNotThrow(() => W.buildSketch("anything"));
  const s = W.buildSketch("anything");
  assert.deepEqual(JSON.parse(JSON.stringify(s.positive_facets)), {});
  assert.deepEqual(JSON.parse(JSON.stringify(s.hard_filters)), {});
});

test("buildSid via runPipeline: recipe with empty flavors falls back to 'default'", () => {
  // Mutate one recipe in the VM context to simulate missing flavors,
  // then confirm SID does not contain the literal string 'undefined'.
  const target = W.RECIPES.find(r => r.id === 113);
  const saved = target.flavors;
  target.flavors = [];
  try {
    const res = W.runPipeline({
      query: "fresh light lunch", liked: [113], disliked: [], hardFilters: {}, topK: 3,
    });
    for (const it of res.conf.items) {
      assert.ok(!it.sid_string.includes("undefined"), `SID has undefined: ${it.sid_string}`);
    }
  } finally {
    target.flavors = saved;
  }
});

test("buildSketch: 'hearty but not too heavy' triggers richness ambiguity note", () => {
  const s = W.buildSketch("hearty but not too heavy", [], [], {});
  assert.ok(s.ambiguity_notes.some(n => n.includes("ambiguous richness")));
});

// ---------- 2.2 Semantic Search + hard filter ----------

test("semanticSearch: dietary_style hard filter drops non-matching recipes with reason", () => {
  const sk = W.buildSketch("", [], [], { dietary_style: ["vegan"] });
  const r = W.semanticSearch(sk);
  for (const c of r.top30) {
    assert.ok(c.dietary.includes("vegan"), `surviving must be vegan: ${c.title}`);
  }
  for (const d of r.dropped) {
    assert.match(d.reason, /^missing dietary:vegan/);
  }
});

test("semanticSearch: max_time filter respected", () => {
  const sk = W.buildSketch("", [], [], { max_time: 25 });
  const r = W.semanticSearch(sk);
  for (const c of r.top30) assert.ok(c.time <= 25, `${c.title} time=${c.time}`);
});

test("semanticSearch: top30 ≤ 30 and every score ≥ 0", () => {
  const sk = W.buildSketch("rich umami", [], [], {});
  const r = W.semanticSearch(sk);
  assert.ok(r.top30.length <= 30);
  assert.ok(r.top100.length <= 100);
  for (const c of r.top30) assert.ok(c.score >= 0);
});

test("semanticSearch: CF features (popularity, cooccurrence) attached on top30", () => {
  const sk = W.buildSketch("", [110, 120], [], {});  // both Italian
  sk._liked = [110, 120];
  const r = W.semanticSearch(sk);
  for (const c of r.top30) {
    assert.equal(typeof c.popularity, "number");
    assert.equal(typeof c.cooccurrence, "number");
  }
  // Italian survivors should have cooccurrence > 0 (matches liked Italian items)
  const italians = r.top30.filter(c => c.cuisine === "Italian");
  if (italians.length) assert.ok(italians.some(c => c.cooccurrence > 0));
});

// ---------- 2.3 Zero-Shot Rerank ----------

test("zeroShotRerank: 5 passes by default, each ≤10 items, 1-indexed", () => {
  const sk = W.buildSketch("creamy", [], [], {});
  sk._liked = [];
  const search = W.semanticSearch(sk);
  const rr = W.zeroShotRerank(search.top30, sk);
  assert.equal(rr.passes.length, 5);
  for (const p of rr.passes) {
    assert.ok(p.length <= 10);
    for (const idx of p) assert.ok(idx >= 1, "passes must be 1-indexed");
  }
});

test("zeroShotRerank: rationale + matchedPrefs keyed per candidate (1-indexed)", () => {
  const sk = W.buildSketch("creamy", [], [], {});
  sk._liked = [];
  const search = W.semanticSearch(sk);
  const rr = W.zeroShotRerank(search.top30, sk);
  for (let i = 1; i <= search.top30.length; i++) {
    assert.equal(typeof rr.rationales[i], "string");
    assert.ok(Array.isArray(rr.matchedPrefs[i]));
  }
});

// ---------- 2.4 MSCP confidence + grounding ----------

test("computeConfidenceAndGround: items ≤ topK, MSCP ∈ [0,1], band classification correct", () => {
  const sk = W.buildSketch("creamy", [], [], {});
  sk._liked = [];
  const search = W.semanticSearch(sk);
  const rr = W.zeroShotRerank(search.top30, sk);
  const conf = W.computeConfidenceAndGround(search.top30, rr, 3);
  assert.ok(conf.items.length <= 3);
  for (const it of conf.items) {
    assert.ok(it.mscp >= 0 && it.mscp <= 1, `mscp=${it.mscp}`);
    const expected = it.mscp >= 0.8 ? "HIGH" : it.mscp >= 0.5 ? "MEDIUM" : "LOW";
    assert.equal(it.confidence_band, expected);
  }
});

test("computeConfidenceAndGround: SID matches `SID::cuisine::dish::flavor::id` format", () => {
  const sk = W.buildSketch("umami", [], [], {});
  sk._liked = [];
  const search = W.semanticSearch(sk);
  const rr = W.zeroShotRerank(search.top30, sk);
  const conf = W.computeConfidenceAndGround(search.top30, rr, 3);
  for (const it of conf.items) {
    assert.match(it.sid_string, /^SID::[a-z-]+::[a-z-]+::[a-z-]+::\d+$/);
    assert.ok(Array.isArray(it.sid_path) && it.sid_path.length === 3);
    for (const level of it.sid_path) {
      assert.ok(Number.isInteger(level) && level >= 0 && level <= 255,
        `sid_path level out of range: ${level}`);
    }
  }
});

test("computeConfidenceAndGround: ranks are 1..N consecutive, allVotes sorted desc", () => {
  const sk = W.buildSketch("umami", [], [], {});
  sk._liked = [];
  const search = W.semanticSearch(sk);
  const rr = W.zeroShotRerank(search.top30, sk);
  const conf = W.computeConfidenceAndGround(search.top30, rr, 3);
  conf.items.forEach((it, i) => assert.equal(it.rank, i + 1));
  for (let i = 1; i < conf.allVotes.length; i++) {
    assert.ok(conf.allVotes[i - 1].votes >= conf.allVotes[i].votes);
  }
});

// ---------- End-to-end ----------

test("runPipeline: cozy-vegetarian preset → all top items are vegetarian", () => {
  const result = W.runPipeline({
    query: "I want hearty but not too heavy comfort food for a weeknight. Vegetarian.",
    liked: [110, 111], disliked: [], hardFilters: { dietary_style: ["vegetarian"] }, topK: 3,
  });
  assert.ok(result.conf.items.length >= 1);
  for (const it of result.conf.items) {
    assert.ok(it.recipe.dietary.includes("vegetarian"), `${it.recipe.title} not vegetarian`);
  }
});

test("runPipeline: spicy-quick gluten-free preset → all top items are gluten-free", () => {
  const result = W.runPipeline({
    query: "Something spicy that I can make fast. No gluten.",
    liked: [117, 105], disliked: [104], hardFilters: { dietary_style: ["gluten-free"] }, topK: 3,
  });
  assert.ok(result.conf.items.length >= 1);
  for (const it of result.conf.items) {
    assert.ok(it.recipe.dietary.includes("gluten-free"), `${it.recipe.title} not GF`);
  }
});

test("runPipeline: returns sketch/search/rerank/conf/timings; timings include simulated values", () => {
  const result = W.runPipeline({
    query: "fresh light lunch", liked: [], disliked: [], hardFilters: {}, topK: 3,
  });
  for (const k of ["sketch", "search", "rerank", "conf", "timings"]) {
    assert.ok(result[k] != null, `missing ${k}`);
  }
  for (const k of ["simSketch", "simRetrieval", "simRerank", "simConfidence"]) {
    assert.equal(typeof result.timings[k], "number");
    assert.ok(result.timings[k] > 0);
  }
});

test("runPipeline: conf.query_sid exposes sid_string and sid_path with integer levels", () => {
  const result = W.runPipeline({
    query: "I want hearty but not too heavy comfort food for a weeknight. Vegetarian.",
    liked: [110, 111], disliked: [], hardFilters: { dietary_style: ["vegetarian"] }, topK: 3,
  });
  const qs = result.conf.query_sid;
  assert.ok(qs && typeof qs === "object", "conf.query_sid must be an object");
  assert.match(qs.sid_string, /^QSID::/);
  assert.ok(Array.isArray(qs.sid_path) && qs.sid_path.length === 3);
  for (const level of qs.sid_path) {
    assert.ok(Number.isInteger(level) && level >= 0 && level <= 255,
      `query_sid level out of range: ${level}`);
  }
});

test("runPipeline: buildQuerySid falls back to 'any' when a sketch facet is missing", () => {
  // Empty query and no liked items → no positive_facets beyond defaults.
  const result = W.runPipeline({
    query: "", liked: [], disliked: [], hardFilters: {}, topK: 3,
  });
  assert.ok(result.conf.query_sid.sid_string.includes("any"),
    `expected 'any' fallback, got ${result.conf.query_sid.sid_string}`);
});
