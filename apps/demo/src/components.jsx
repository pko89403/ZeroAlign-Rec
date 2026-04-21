/* Shared React components for ZeroAlign-Rec demo.
 * All components accept a locale table L (window.I18N.en or .kr).
 * Exported to window at the bottom so thin entry files can use them. */

const { useState, useEffect, useRef } = React;

// ===== Utilities =====
function shade(hex, amt) {
  const h = hex.replace("#", "");
  const r = parseInt(h.slice(0,2),16), g = parseInt(h.slice(2,4),16), b = parseInt(h.slice(4,6),16);
  const clamp = v => Math.max(0, Math.min(255, Math.round(v)));
  return `rgb(${clamp(r*(1+amt))},${clamp(g*(1+amt))},${clamp(b*(1+amt))})`;
}

function avgMscp(items) {
  return items.length ? (items.reduce((s,i)=>s+i.mscp,0)/items.length).toFixed(2) : "—";
}

// Build a URL pointing at the same page but with `lang` overridden, preserving
// every other query parameter (e.g. utm_source) the user arrived with.
function buildLangHref(targetLang) {
  const params = new URLSearchParams(location.search);
  params.set("lang", targetLang);
  return "?" + params.toString();
}

// ===== Icons =====
const BrandMark = () => (
  <svg viewBox="0 0 512 512" fill="none">
    <circle cx="256" cy="256" r="200" stroke="#67E8F9" strokeWidth="16" opacity="0.3"/>
    <path d="M256 136V376" stroke="#A78BFA" strokeWidth="24" strokeLinecap="round"/>
    <path d="M256 178L180 208L316 284L236 334" stroke="#F8FAFC" strokeWidth="32" strokeLinecap="round" strokeLinejoin="round"/>
    <circle cx="256" cy="256" r="46" fill="#0B1120" stroke="#34D399" strokeWidth="16"/>
  </svg>
);

const PlayIcon = () => (
  <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8 5v14l11-7z"/></svg>
);

// ===== JSON preview =====
// Escape HTML BEFORE the regex highlight pass so user-supplied strings
// (e.g. sketch.summary, which echoes the query textarea) cannot inject
// markup via dangerouslySetInnerHTML. The highlight regexes still match
// because JSON.stringify's quote characters are not escaped.
const escapeHtml = s =>
  s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

function JsonView({ data, label }) {
  const json = escapeHtml(JSON.stringify(data, null, 2));
  const highlighted = json
    .replace(/("(?:[^"\\]|\\.)*")(\s*:)/g, '<span class="json-key">$1</span>$2')
    .replace(/:\s*("(?:[^"\\]|\\.)*")/g, ': <span class="json-str">$1</span>')
    .replace(/:\s*(-?\d+(?:\.\d+)?)/g, ': <span class="json-num">$1</span>');
  // <pre><code> gives the right semantics; tabIndex makes the scroll
  // container reachable via keyboard.
  return (
    <pre className="json-block" tabIndex={0} role="region" aria-label={label}>
      <code dangerouslySetInnerHTML={{ __html: highlighted }} />
    </pre>
  );
}

// ===== Sidebar =====
function Sidebar({ L, preset, setPreset, query, setQuery, liked, disliked, toggleLiked, toggleDisliked, filters, setFilters, topK, setTopK, onRun, running }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark"><BrandMark /></div>
        <div>
          <div className="brand-name">ZeroAlign-Rec</div>
          <div className="brand-sub">{L.sb.brandSub}</div>
        </div>
      </div>

      <div className="sb-section">
        <div className="sb-label" id="sb-presets-label">{L.sb.presets}</div>
        <div className="preset-list" role="radiogroup" aria-labelledby="sb-presets-label">
          {L.presets.map(p => (
            <button key={p.id} type="button" role="radio" aria-checked={preset === p.id}
              className={"preset-btn" + (preset === p.id ? " active" : "")} onClick={() => setPreset(p.id)}>
              {p.label}
              <span className="kw">{p.sub}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="sb-section">
        <label className="sb-label" htmlFor="sb-query">{L.sb.query}</label>
        <textarea id="sb-query" className="query" value={query} onChange={e => setQuery(e.target.value)} placeholder={L.sb.queryPh} />
      </div>

      <div className="sb-section">
        <div className="sb-label" id="sb-history-label">{L.sb.history}</div>
        <div className="item-list" role="group" aria-labelledby="sb-history-label">
          {window.RECIPES.slice(0, 14).map(r => (
            <div className="item-row" key={r.id}>
              <span className="item-dot" style={{ "--img": r.img }} />
              <span className="item-name">{r.title}</span>
              <button type="button" aria-pressed={liked.includes(r.id)} aria-label={L.a11y.likeBtn(r.title)}
                className={"item-btn" + (liked.includes(r.id) ? " on-pos" : "")} onClick={() => toggleLiked(r.id)}>+</button>
              <button type="button" aria-pressed={disliked.includes(r.id)} aria-label={L.a11y.dislikeBtn(r.title)}
                className={"item-btn" + (disliked.includes(r.id) ? " on-neg" : "")} onClick={() => toggleDisliked(r.id)}>−</button>
            </div>
          ))}
        </div>
      </div>

      <div className="sb-section">
        <div className="sb-label" id="sb-filters-label">{L.sb.filters}</div>
        <div className="chip-row" role="group" aria-labelledby="sb-filters-label">
          {window.TAXONOMY.dietary_style.map(d => {
            const on = (filters.dietary_style || []).includes(d);
            return <button key={d} type="button" aria-pressed={on}
              className={"chip" + (on ? " filter" : "")} onClick={() => {
              const cur = filters.dietary_style || [];
              const next = on ? cur.filter(x => x !== d) : [...cur, d];
              setFilters({ ...filters, dietary_style: next });
            }}>{L.dietLabel(d)}</button>;
          })}
        </div>
      </div>

      <div className="sb-section">
        <label className="sb-label" htmlFor="sb-topk">{L.sb.topK}</label>
        <div className="slider-row">
          <div className="slider-head"><span className="muted">{L.sb.topKSub}</span><span className="slider-value">{topK}</span></div>
          <input id="sb-topk" type="range" min={1} max={6} value={topK} onChange={e => setTopK(+e.target.value)} />
        </div>
      </div>

      <button className={"run-btn" + (running ? " running" : "")} onClick={onRun} disabled={running}>
        <PlayIcon /> {running ? L.sb.runBusy : L.sb.runIdle}
      </button>
    </aside>
  );
}

// ===== Tab bar =====
function TabBar({ L, active, setActive, result }) {
  // aria-disabled + tabindex=-1 keeps the queued tabs visible to AT and
  // skipped from Tab order, instead of HTML `disabled` (which makes them
  // disappear from focus traversal entirely).
  return (
    <div className="tabbar" role="tablist">
      {L.tabs.map(t => {
        const ready = result || t.id === "overview";
        const isActive = active === t.id;
        return (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            aria-current={isActive ? "page" : undefined}
            aria-disabled={!ready}
            tabIndex={ready ? 0 : -1}
            className={"tab" + (isActive ? " active" : "") + (!ready ? " disabled" : "")}
            onClick={() => ready && setActive(t.id)}
          >
            <span className="tab-num">{t.num}</span>
            <span className="tab-label">{t.label}</span>
            <span className="tab-sub">{t.sub}</span>
          </button>
        );
      })}
    </div>
  );
}

// ===== Stage strip =====
function PipelineStrip({ L, stage, timings }) {
  return (
    <div className="pipeline">
      {L.pipeline.map((s, i) => {
        const state = stage > i ? "done" : stage === i ? "active" : "";
        const t = timings?.[s.tKey];
        return (
          <div className={`stage ${state}`} key={i}>
            <div className="stage-head">
              <span className="stage-num">MODULE {s.num}</span>
              <span className="stage-status" />
            </div>
            <div className="stage-title">{s.title}</div>
            <div className="stage-sub">{s.sub}</div>
            <div className="stage-metric">
              {t != null && state === "done"
                ? <><span className="m-value">{L.stageDone(t)}</span> · {L.runtimeTag}</>
                : state === "active" ? L.stageActive : L.stageQueued}
            </div>
          </div>
        );
      })}
    </div>
  );
}

// ===== Panel 2.1 — Interest Sketch =====
function Panel21({ L, sketch }) {
  if (!sketch) return null;
  const hasPos = Object.keys(sketch.positive_facets).length > 0;
  const hasNegOrHF = Object.keys(sketch.negative_facets).length > 0 || Object.keys(sketch.hard_filters).length > 0;
  return (
    <div className="module-panel">
      <div className="module-panel-head">
        <h3 className="module-panel-title"><span className="num">MODULE 2.1</span>{L.p21.title}</h3>
        <span className="module-panel-sub">{L.p21.sub}</span>
      </div>
      <div className="kvp"><div className="kvp-key">{L.p21.kvpSummary}</div><div className="kvp-val">{sketch.summary}</div></div>
      {sketch.ambiguity_notes.length > 0 && (
        <div className="kvp"><div className="kvp-key">{L.p21.kvpAmbiguity}</div><div className="kvp-val muted">{sketch.ambiguity_notes.join(" · ")}</div></div>
      )}
      <div style={{ height: 14 }} />
      <div className="sketch-grid">
        <div className="sketch-block">
          <h4>{L.p21.positive}</h4>
          {Object.entries(sketch.positive_facets).map(([f, vals]) => (
            <div className="facet-row" key={f}>
              <span className="facet-name">{f}</span>
              <div className="chip-row">{vals.map(v => <span className="chip pos" key={v}>{v}</span>)}</div>
            </div>
          ))}
          {!hasPos && <div className="muted" style={{fontSize:11}}>{L.p21.emptyPos}</div>}
        </div>
        <div className="sketch-block">
          <h4>{L.p21.negative}</h4>
          {Object.entries(sketch.negative_facets).map(([f, vals]) => (
            <div className="facet-row" key={f}>
              <span className="facet-name">{f}</span>
              <div className="chip-row">{vals.map(v => <span className="chip neg" key={v}>¬{v}</span>)}</div>
            </div>
          ))}
          {Object.entries(sketch.hard_filters).map(([f, vals]) => (
            <div className="facet-row" key={f}>
              <span className="facet-name">{f}</span>
              <div className="chip-row">{vals.map(v => <span className="chip filter" key={v}>={L.dietLabel(v)}</span>)}</div>
            </div>
          ))}
          {!hasNegOrHF && <div className="muted" style={{fontSize:11}}>{L.p21.emptyNegHF}</div>}
        </div>
      </div>
    </div>
  );
}

// ===== Panel 2.2 — Semantic search =====
function Panel22({ L, search }) {
  if (!search) return null;
  const { top30, dropped } = search;
  return (
    <div className="module-panel">
      <div className="module-panel-head">
        <h3 className="module-panel-title"><span className="num">MODULE 2.2</span>{L.p22.title}</h3>
        <span className="module-panel-sub">{L.p22.sub}</span>
      </div>
      <div className="candidate-split">
        <div className="candidate-col">
          <h4>{L.p22.surviving} <span className="count">{top30.length}/30</span></h4>
          <div className="candidate-list">
            {top30.map((c, i) => (
              <div className="cand-item" key={c.id}>
                <div className="cand-rank">{i+1}</div>
                <div className="cand-thumb" style={{ "--img": c.img }}/>
                <div>
                  <div className="cand-title">{c.title}</div>
                  <div className="cand-meta">{L.p22.candMeta(c)}</div>
                </div>
                <div className="cand-score">{c.score.toFixed(3)}</div>
              </div>
            ))}
          </div>
        </div>
        <div className="candidate-col">
          <h4>{L.p22.dropped} <span className="count">{dropped.length}</span></h4>
          <div className="candidate-list">
            {dropped.slice(0, 30).map(d => (
              <div className="cand-item dropped" key={d.id}>
                <div className="cand-rank">—</div>
                <div/>
                <div>
                  <div className="cand-title">{d.title}</div>
                  <div className="cand-meta">{d.reason}</div>
                </div>
                <div className="cand-score">drop</div>
              </div>
            ))}
            {dropped.length === 0 && <div className="muted" style={{fontSize:11, padding:10}}>{L.p22.noDrop}</div>}
          </div>
        </div>
      </div>
    </div>
  );
}

// ===== Panel 2.3 — Rerank passes =====
function Panel23({ L, rerank, conf }) {
  if (!rerank || !conf) return null;
  const topSet = new Set((conf.items || []).map(x => x.idx));
  return (
    <div className="module-panel">
      <div className="module-panel-head">
        <h3 className="module-panel-title"><span className="num">MODULE 2.3</span>{L.p23.title}</h3>
        <span className="module-panel-sub">{L.p23.sub}</span>
      </div>
      <div className="passes-grid">
        {rerank.passes.map((p, pi) => (
          <div className="pass-row" key={pi}>
            <span className="pass-label">{L.p23.pass} {pi+1}</span>
            <div className="pass-tokens">
              {p.map((idx, pos) => (
                <span key={pos} className={"pass-tok " + (topSet.has(idx) ? "top" : pos < 3 ? "highlight" : "")}>{idx}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--ink-subtle)", marginTop: 14, letterSpacing: "0.04em" }}>
        {L.p23.footLeft}<span style={{color:"var(--ink)"}}>{L.p23.footModel}</span>{L.p23.footRight}
      </div>
    </div>
  );
}

// ===== Panel 2.4 — MSCP confidence =====
function Panel24({ L, conf, candidates }) {
  if (!conf) return null;
  const maxVote = conf.allVotes[0]?.votes || 1;
  return (
    <div className="module-panel">
      <div className="module-panel-head">
        <h3 className="module-panel-title"><span className="num">MODULE 2.4</span>{L.p24.title}</h3>
        <span className="module-panel-sub">{L.p24.sub}</span>
      </div>
      <div style={{ fontFamily: "var(--mono)", fontSize: 10, color: "var(--ink-subtle)", marginBottom: 10, letterSpacing: "0.04em" }}>
        {L.p24.voteHeader}
      </div>
      <div className="votes-grid">
        {conf.allVotes.slice(0, 10).map((v) => {
          const c = candidates[v.idx - 1];
          const appearTopK = conf.items.find(x => x.idx === v.idx);
          const mscp = appearTopK ? appearTopK.mscp : 0;
          const band = mscp >= 0.8 ? "HIGH" : mscp >= 0.5 ? "MEDIUM" : mscp > 0 ? "LOW" : "—";
          return (
            <div className="vote-row" key={v.idx}>
              <span className="vote-idx">#{v.idx}</span>
              <div className="vote-bar">
                <div className="vote-bar-fill" style={{ width: `${(v.votes/maxVote)*100}%` }} />
                <span className="vote-bar-label">{c?.title}</span>
              </div>
              <span className="vote-mscp">{L.p24.mscpLabel} {mscp.toFixed(2)}</span>
              <span className={"vote-band band-" + band}>{L.p24.band[band] || band}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ===== Final delivery cards =====
function FinalDelivery({ L, conf }) {
  if (!conf) return null;
  return (
    <div className="module-panel">
      <div className="module-panel-head">
        <h3 className="module-panel-title"><span className="num">{L.tabs[1].num}</span>{L.final.title}</h3>
        <span className="module-panel-sub">{L.final.sub}</span>
      </div>
      <div className="final-cards">
        {conf.items.map(item => {
          const r = item.recipe;
          const bandLabel = L.p24.band[item.confidence_band] || item.confidence_band;
          return (
            <div key={item.idx} className={`final-card rank-${item.rank}`}>
              <div className="final-img" style={{ "--img-a": r.img, "--img-b": shade(r.img, -0.25) }}>
                <div className="final-rank">#{item.rank}</div>
                <div className={"final-band " + item.confidence_band}>{L.final.bandPrefix}{bandLabel} · {item.mscp.toFixed(2)}</div>
              </div>
              <div className="final-body">
                <h4 className="final-title">{r.title}</h4>
                <div className="final-meta">{L.final.meta(r)}</div>
                <div className="final-rationale">{item.rationale}</div>
                <div className="final-matched">
                  {item.matched_preferences.map((m, i) => <span key={i} className="matched-chip">{m}</span>)}
                </div>
                <div className="final-bottom">
                  <span>{L.final.bootstrap(item.bootstrap_support)}</span>
                  <span className="final-sid">{item.sid}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ===== Metrics strip =====
function MetricsStrip({ L, result }) {
  const total = result.timings.simSketch + result.timings.simRetrieval + result.timings.simRerank + result.timings.simConfidence;
  return (
    <div className="metrics">
      <div className="metric"><span className="metric-label">{L.metrics.totalLatency}</span><span className="metric-val accent">{total}ms</span></div>
      <div className="metric"><span className="metric-label">{L.metrics.retrieved}</span><span className="metric-val">Top-{result.search.top100.length} → Top-{result.search.top30.length}</span></div>
      <div className="metric"><span className="metric-label">{L.metrics.droppedByHF}</span><span className="metric-val">{result.search.dropped.length}</span></div>
      <div className="metric"><span className="metric-label">{L.metrics.rerankPasses}</span><span className="metric-val">{result.rerank.passes.length}</span></div>
      <div className="metric"><span className="metric-label">{L.metrics.avgMscp}</span><span className="metric-val">{avgMscp(result.conf.items)}</span></div>
      <div className="metric"><span className="metric-label">{L.metrics.ood}</span><span className="metric-val" style={{color:"var(--emerald)"}}>0%</span></div>
    </div>
  );
}

// ===== Overview grid =====
function OverviewGrid({ L, result, setActiveTab }) {
  const posCount = Object.values(result.sketch.positive_facets).reduce((a,b)=>a+b.length,0);
  const hfCount = Object.keys(result.sketch.hard_filters).length;
  const cards = [
    { tab: "m21", num: "2.1", title: L.overview.m21Title,
      body: [L.overview.m21Body1(posCount), L.overview.m21Body2(hfCount)] },
    { tab: "m22", num: "2.2", title: L.overview.m22Title,
      body: [L.overview.m22Body1(result.search.top30.length), L.overview.m22Body2(result.search.dropped.length)] },
    { tab: "m23", num: "2.3", title: L.overview.m23Title,
      body: [L.overview.m23Body1(result.rerank.passes.length), L.overview.m23Body2] },
    { tab: "m24", num: "2.4", title: L.overview.m24Title,
      body: [L.overview.m24Body1(avgMscp(result.conf.items)), L.overview.m24Body2] },
  ];
  return (
    <div className="overview-grid">
      {cards.map(c => (
        <button key={c.tab} type="button" className="overview-card" onClick={() => setActiveTab(c.tab)}>
          <div className="oc-num">{c.num}</div>
          <div className="oc-title">{c.title}</div>
          <div className="oc-body">
            {c.body.map((b, i) => <span key={i}>{b}</span>)}
          </div>
          <div className="oc-foot">{L.overview.cta}</div>
        </button>
      ))}
    </div>
  );
}

// ===== JSON tab body =====
function JsonTab({ L, result, topK }) {
  const payload = {
    sketch: {
      summary: result.sketch.summary,
      positive_facets: result.sketch.positive_facets,
      negative_facets: result.sketch.negative_facets,
      hard_filters: result.sketch.hard_filters,
      ambiguity_notes: result.sketch.ambiguity_notes,
    },
    items: result.conf.items.map(i => ({
      recipe_id: i.recipe.id,
      sid_string: i.sid,
      rank: i.rank,
      title: i.recipe.title,
      rationale: i.rationale,
      matched_preferences: i.matched_preferences,
      confidence_band: i.confidence_band,
      mscp: +i.mscp.toFixed(3),
      mapping_mode: i.mapping_mode,
      bootstrap_support: i.bootstrap_support,
      popularity: i.recipe.popularity,
      cooccurrence_with_history: i.recipe.cooccurrence,
    })),
    rerank_summary: L.json.rerankSummary(topK),
    confidence_summary: result.conf.items.every(i => i.confidence_band === "HIGH") ? L.json.confAllHigh : L.json.confMixed,
    selected_candidate_indices: result.conf.items.map(i => i.idx),
  };
  return (
    <div className="module-panel">
      <div className="module-panel-head">
        <h3 className="module-panel-title"><span className="num">API</span>{L.json.title}</h3>
        <span className="module-panel-sub">{L.json.sub}</span>
      </div>
      <JsonView data={payload} label={L.a11y.jsonRegion} />
    </div>
  );
}

// ===== App shell =====
function App({ L }) {
  const presets = L.presets;
  const [preset, setPreset] = useState(presets[0].id);
  const [query, setQuery] = useState(presets[0].query);
  const [liked, setLiked] = useState(presets[0].liked);
  const [disliked, setDisliked] = useState(presets[0].disliked);
  const [filters, setFilters] = useState(presets[0].filters);
  const [topK, setTopK] = useState(presets[0].topK);
  const [activeTab, setActiveTab] = useState("overview");
  const [result, setResult] = useState(null);
  const [running, setRunning] = useState(false);
  const [stage, setStage] = useState(-1);

  useEffect(() => {
    const p = presets.find(x => x.id === preset);
    if (!p) return;
    setQuery(p.query);
    setLiked(p.liked);
    setDisliked(p.disliked);
    setFilters(p.filters);
    setTopK(p.topK);
  }, [preset]);

  const toggleLiked = id => setLiked(l => l.includes(id) ? l.filter(x=>x!==id) : [...l, id]);
  const toggleDisliked = id => setDisliked(l => l.includes(id) ? l.filter(x=>x!==id) : [...l, id]);

  const timeoutsRef = useRef([]);
  const cancelPending = () => {
    timeoutsRef.current.forEach(clearTimeout);
    timeoutsRef.current = [];
  };

  const onRun = () => {
    cancelPending();
    setRunning(true);
    setStage(-1);
    setResult(null);
    setActiveTab("overview");
    const res = window.runPipeline({ query, liked, disliked, hardFilters: filters, topK });
    const delays = [res.timings.simSketch, res.timings.simRetrieval, res.timings.simRerank, res.timings.simConfidence];
    let cum = 0;
    delays.forEach((d, i) => {
      timeoutsRef.current.push(setTimeout(() => setStage(i), cum));
      cum += d;
    });
    timeoutsRef.current.push(setTimeout(() => {
      setResult(res);
      setStage(4);
      setRunning(false);
      setActiveTab("final");
    }, cum));
  };

  useEffect(() => { onRun(); return cancelPending; /* eslint-disable-next-line */ }, []);

  const renderTab = () => {
    if (!result) {
      const [a, em, b] = L.idleText;
      return <div className="empty">{a}<em>{em}</em>{b}</div>;
    }
    switch (activeTab) {
      case "overview":
        return (
          <>
            <PipelineStrip L={L} stage={stage} timings={result?.timings} />
            <MetricsStrip L={L} result={result} />
            <OverviewGrid L={L} result={result} setActiveTab={setActiveTab} />
          </>
        );
      case "final": return <FinalDelivery L={L} conf={result.conf} />;
      case "m21":   return <Panel21 L={L} sketch={result.sketch} />;
      case "m22":   return <Panel22 L={L} search={result.search} />;
      case "m23":   return <Panel23 L={L} rerank={result.rerank} conf={result.conf} />;
      case "m24":   return <Panel24 L={L} conf={result.conf} candidates={result.search.top30} />;
      case "json":  return <JsonTab L={L} result={result} topK={topK} />;
      default: return null;
    }
  };

  return (
    <div className="app">
      <Sidebar
        L={L}
        preset={preset} setPreset={setPreset}
        query={query} setQuery={setQuery}
        liked={liked} disliked={disliked}
        toggleLiked={toggleLiked} toggleDisliked={toggleDisliked}
        filters={filters} setFilters={setFilters}
        topK={topK} setTopK={setTopK}
        onRun={onRun} running={running}
      />

      <main className="main">
        <div className="topbar">
          <div>
            <h1 className="topbar-title">
              <span className="ac-cyan">{L.pageTitle.a}</span> <span className="ac-violet">{L.pageTitle.b}</span> {L.pageTitle.c}
            </h1>
            <div className="topbar-sub">{L.pageSub}</div>
          </div>
          <a
            href={buildLangHref(L.otherLang.lang)}
            hrefLang={L.otherLang.lang === "kr" ? "ko" : "en"}
            aria-label={L.a11y.langSwitchTo}
            className="lang-switch"
          >{L.otherLang.label}</a>
        </div>

        <TabBar L={L} active={activeTab} setActive={setActiveTab} result={result} />

        {renderTab()}
      </main>
    </div>
  );
}

// Expose App to thin entry scripts (Babel scopes each <script> separately)
window.ZeroAlignApp = App;
