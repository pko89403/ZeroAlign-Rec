/* Shared loader: evaluates the demo's data + pipeline scripts in a fresh
 * VM context that simulates the browser `window` global, then returns it. */
const fs = require("fs");
const path = require("path");
const vm = require("vm");

function loadDemoGlobals() {
  const ctx = { performance: { now: () => Date.now() } };
  ctx.window = ctx;
  vm.createContext(ctx);

  const root = path.join(__dirname, "..");
  for (const rel of ["data/taxonomy.js", "data/recipes.js", "data/pipeline.js"]) {
    const src = fs.readFileSync(path.join(root, rel), "utf8");
    vm.runInContext(src, ctx, { filename: rel });
  }
  return ctx;
}

function loadI18N() {
  const ctx = { window: {} };
  ctx.window.window = ctx.window;
  vm.createContext(ctx);
  const src = fs.readFileSync(path.join(__dirname, "..", "src/i18n.js"), "utf8");
  vm.runInContext(src, ctx, { filename: "src/i18n.js" });
  return ctx.window.I18N;
}

module.exports = { loadDemoGlobals, loadI18N };
