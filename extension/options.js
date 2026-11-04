const DEFAULT_APP_URL = "https://bubu-hkbu.streamlit.app";
const DEFAULT_LANG = "zh-CN";
const LANGS = ["zh-CN", "zh-TW", "en"];

const input = document.getElementById("appUrl");
const langSel = document.getElementById("appLang");
const status = document.getElementById("status");

function normalizeAppUrl(raw) {
  const s = String(raw || "").trim().replace(/\/$/, "");
  if (!s || /localhost|127\.0\.0\.1/i.test(s)) return DEFAULT_APP_URL;
  return s;
}

chrome.storage.sync.get({ bubu_app_url: DEFAULT_APP_URL, bubu_lang: DEFAULT_LANG }, (data) => {
  input.value = normalizeAppUrl(data.bubu_app_url);
  langSel.value = LANGS.includes(data.bubu_lang) ? data.bubu_lang : DEFAULT_LANG;
});

document.getElementById("save").addEventListener("click", () => {
  const url = normalizeAppUrl(input.value);
  const lang = LANGS.includes(langSel.value) ? langSel.value : DEFAULT_LANG;
  input.value = url;
  chrome.storage.sync.set({ bubu_app_url: url, bubu_lang: lang }, () => {
    status.textContent =
      lang === "en" ? "Saved" : lang === "zh-TW" ? "已儲存" : "已保存";
  });
});
