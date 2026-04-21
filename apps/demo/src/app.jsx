/* Single entry — picks language from ?lang= URL param, then navigator.language.
 * Accepts BCP-47 alias `?lang=ko` for the Korean bundle. */
const lang = (() => {
  let param = new URLSearchParams(location.search).get("lang");
  if (param === "ko") param = "kr";
  if (param === "en" || param === "kr") return param;
  return navigator.language?.toLowerCase().startsWith("ko") ? "kr" : "en";
})();

const L = window.I18N[lang];
document.documentElement.lang = lang === "kr" ? "ko" : "en";
document.title = L.docTitle;

ReactDOM.createRoot(document.getElementById("root")).render(
  <window.ZeroAlignApp L={L} />
);
