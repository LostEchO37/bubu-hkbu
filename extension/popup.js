const status = document.getElementById("status");
const langSel = document.getElementById("popupLang");

const LANGS = ["zh-CN", "zh-TW", "en"];
const COPY = {
  "zh-CN": {
    title: "阿Bu · 悬浮球",
    blurb: "应出现在任意 http/https 网页右下角。点分支会打开阿Bu，并尽量带上已登录状态。",
    inject: "在当前页强制显示悬浮球",
    injecting: "注入中…",
    injected: "已注入，请看页面右下角",
    fail: "失败",
    warn1: "1. 扩展「重新加载」后刷新目标网页",
    warn2: "2. 若点开显示没权限：Cloud Sharing 必须 Public，并用 My apps 卡片网址",
    warn3: "3. 先在阿Bu 页登录一次（地址栏会带 auth），再点悬浮球任务才不用重登",
    settings: "设置地址与语言",
    langLabel: "语言",
  },
  "zh-TW": {
    title: "阿Bu · 懸浮球",
    blurb: "應出現在任意 http/https 網頁右下角。點分支會打開阿Bu，並盡量帶上已登入狀態。",
    inject: "在當前頁強制顯示懸浮球",
    injecting: "注入中…",
    injected: "已注入，請看頁面右下角",
    fail: "失敗",
    warn1: "1. 擴充「重新載入」後重新整理目標網頁",
    warn2: "2. 若點開顯示沒權限：Cloud Sharing 必須 Public，並用 My apps 卡片網址",
    warn3: "3. 先在阿Bu 頁登入一次（網址會帶 auth），再點懸浮球任務才不用重登",
    settings: "設定網址與語言",
    langLabel: "語言",
  },
  en: {
    title: "BuBu · Floating orb",
    blurb: "Shows on any http/https page (bottom-right). Branches open BuBu and keep login when possible.",
    inject: "Force-show orb on this page",
    injecting: "Injecting…",
    injected: "Injected — check bottom-right",
    fail: "Failed",
    warn1: "1. Reload the extension, then refresh the page",
    warn2: "2. If you see “no access”: set Cloud Sharing=Public and use the My apps URL",
    warn3: "3. Sign in on BuBu once (URL has auth), then FAB jumps keep the session",
    settings: "App URL & language",
    langLabel: "Language",
  },
};

function applyPopupLang(lang) {
  const c = COPY[lang] || COPY["zh-CN"];
  document.documentElement.lang = lang;
  document.getElementById("title").textContent = c.title;
  document.getElementById("blurb").textContent = c.blurb;
  document.getElementById("inject").textContent = c.inject;
  document.getElementById("warn1").textContent = c.warn1;
  document.getElementById("warn2").textContent = c.warn2;
  document.getElementById("warn3").textContent = c.warn3;
  document.getElementById("settingsLink").textContent = c.settings;
  document.getElementById("langLabel").textContent = c.langLabel;
  return c;
}

chrome.storage.sync.get({ bubu_lang: "zh-CN" }, (data) => {
  const lang = LANGS.includes(data.bubu_lang) ? data.bubu_lang : "zh-CN";
  langSel.value = lang;
  applyPopupLang(lang);
});

langSel.addEventListener("change", () => {
  const lang = LANGS.includes(langSel.value) ? langSel.value : "zh-CN";
  chrome.storage.sync.set({ bubu_lang: lang }, () => {
    applyPopupLang(lang);
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      const tab = tabs[0];
      if (tab?.id != null) {
        chrome.tabs.sendMessage(tab.id, { type: "bubu-remount" }, () => {
          void chrome.runtime.lastError;
        });
      }
    });
  });
});

document.getElementById("inject").addEventListener("click", () => {
  const lang = LANGS.includes(langSel.value) ? langSel.value : "zh-CN";
  const c = COPY[lang] || COPY["zh-CN"];
  status.textContent = c.injecting;
  chrome.runtime.sendMessage({ type: "bubu-inject-active" }, (res) => {
    if (chrome.runtime.lastError) {
      status.textContent = chrome.runtime.lastError.message;
      return;
    }
    status.textContent = res?.ok ? c.injected : res?.error || c.fail;
  });
});
