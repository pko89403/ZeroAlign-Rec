const { test } = require("node:test");
const assert = require("node:assert/strict");
const { loadI18N } = require("./_loader.cjs");

const I = loadI18N();
const { en, kr } = I;

/* Recursively flatten an object into "a.b.c" leaf paths.
 * Arrays are expanded by index ("presets.0.id") so structural parity
 * (not value equality) is the assertion. Functions count as leaves. */
function flattenPaths(v, prefix = "") {
  if (v === null || v === undefined) return [prefix];
  if (typeof v === "function") return [prefix];
  if (typeof v !== "object") return [prefix];
  const items = Array.isArray(v) ? v.map((el, i) => [String(i), el]) : Object.entries(v);
  if (items.length === 0) return [prefix];
  return items.flatMap(([k, val]) => flattenPaths(val, prefix ? `${prefix}.${k}` : k));
}

test("EN/KR exist on window.I18N", () => {
  assert.ok(en && typeof en === "object");
  assert.ok(kr && typeof kr === "object");
});

test("EN/KR have identical top-level keys", () => {
  assert.deepEqual(Object.keys(en).sort(), Object.keys(kr).sort());
});

test("EN/KR have identical structural paths (arrays expanded by index)", () => {
  const enPaths = flattenPaths(en).sort();
  const krPaths = flattenPaths(kr).sort();
  // Diff for clearer failure reporting
  const onlyEn = enPaths.filter(p => !krPaths.includes(p));
  const onlyKr = krPaths.filter(p => !enPaths.includes(p));
  assert.deepEqual({ onlyEn, onlyKr }, { onlyEn: [], onlyKr: [] });
});

test("Both languages have 4 presets with matching ids", () => {
  assert.equal(en.presets.length, 4);
  assert.equal(kr.presets.length, 4);
  assert.deepEqual(en.presets.map(p => p.id), kr.presets.map(p => p.id));
});

test("Each preset has same liked/disliked/filters/topK across EN and KR", () => {
  for (let i = 0; i < en.presets.length; i++) {
    const e = en.presets[i], k = kr.presets[i];
    assert.deepEqual(e.liked, k.liked, `presets[${i}].liked diverged`);
    assert.deepEqual(e.disliked, k.disliked, `presets[${i}].disliked diverged`);
    assert.deepEqual(e.filters, k.filters, `presets[${i}].filters diverged`);
    assert.equal(e.topK, k.topK, `presets[${i}].topK diverged`);
  }
});

test("Both languages have 7 tabs with matching ids", () => {
  assert.equal(en.tabs.length, 7);
  assert.equal(kr.tabs.length, 7);
  assert.deepEqual(en.tabs.map(t => t.id), kr.tabs.map(t => t.id));
});

test("docTitle present and otherLang carries target lang code (not URL)", () => {
  // After review fix #5, the URL is built dynamically by buildLangHref so
  // other query params (utm_source, etc.) are preserved on language switch.
  // i18n only stores the target language code + display label.
  assert.match(en.docTitle, /^ZeroAlign-Rec/);
  assert.match(kr.docTitle, /^ZeroAlign-Rec/);
  assert.equal(en.otherLang.lang, "kr");
  assert.equal(kr.otherLang.lang, "en");
  assert.equal(en.otherLang.label, "KR");
  assert.equal(kr.otherLang.label, "EN");
});

test("Pipeline stage tKey values match what runPipeline emits", () => {
  // pipeline[].tKey should be one of the 4 simulated timing keys
  const expected = new Set(["simSketch", "simRetrieval", "simRerank", "simConfidence"]);
  for (const stage of [...en.pipeline, ...kr.pipeline]) {
    assert.ok(expected.has(stage.tKey), `unexpected tKey: ${stage.tKey}`);
  }
});
