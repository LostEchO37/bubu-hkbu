const DEFAULT_APP_URL = "https://bubu-hkbu.streamlit.app";
const DEFAULT_LANG = "zh-CN";
const LANGS = ["zh-CN", "zh-TW", "en"];

function normalizeAppUrl(raw) {
  const s = String(raw || "").trim().replace(/\/$/, "");
  if (!s || /localhost|127\.0\.0\.1/i.test(s)) return DEFAULT_APP_URL;
  return s;
}

async function getAppUrl() {
  const { bubu_app_url } = await chrome.storage.sync.get({ bubu_app_url: DEFAULT_APP_URL });
  const url = normalizeAppUrl(bubu_app_url);
  if (url !== bubu_app_url) {
    await chrome.storage.sync.set({ bubu_app_url: url });
  }
  return url;
}

async function getLang() {
  const { bubu_lang } = await chrome.storage.sync.get({ bubu_lang: DEFAULT_LANG });
  return LANGS.includes(bubu_lang) ? bubu_lang : DEFAULT_LANG;
}

function canInject(url) {
  if (!url) return false;
  try {
    const u = new URL(url);
    if (u.protocol !== "http:" && u.protocol !== "https:") return false;
    const blockHosts = [
      "chrome.google.com",
      "chromewebstore.google.com",
      "microsoftedge.microsoft.com",
    ];
    if (blockHosts.some((h) => u.hostname === h || u.hostname.endsWith("." + h))) return false;
    return true;
  } catch {
    return false;
  }
}

async function injectFab(tabId) {
  try {
    await chrome.scripting.executeScript({
      target: { tabId },
      files: ["content.js"],
    });
  } catch {
    /* chrome://, Web Store, PDF, etc. */
  }
}

async function resolveAuth(appOrigin) {
  const { bubu_auth } = await chrome.storage.local.get({ bubu_auth: "" });
  if (bubu_auth) return String(bubu_auth);

  const tabs = await chrome.tabs.query({});
  for (const tab of tabs) {
    try {
      const u = new URL(tab.url || "");
      if (u.origin !== appOrigin) continue;
      const auth = u.searchParams.get("auth");
      if (auth) {
        await chrome.storage.local.set({ bubu_auth: auth });
        return auth;
      }
    } catch {
      /* continue */
    }
  }
  return "";
}

async function openFab(action) {
  const base = await getAppUrl();
  const lang = await getLang();
  const url = new URL(base);
  const auth = await resolveAuth(url.origin);
  if (auth) url.searchParams.set("auth", auth);
  url.searchParams.set("lang", lang);

  if (action === "chat") {
    url.searchParams.set("wake", "1");
  } else if (action) {
    url.searchParams.set("fab", action);
  }

  const target = url.toString();
  const tabs = await chrome.tabs.query({});
  const hit = tabs.find((t) => {
    try {
      const u = new URL(t.url || "");
      return u.origin === url.origin;
    } catch {
      return false;
    }
  });

  if (hit?.id != null) {
    await chrome.tabs.update(hit.id, { url: target, active: true });
    if (hit.windowId != null) await chrome.windows.update(hit.windowId, { focused: true });
    return;
  }
  await chrome.tabs.create({ url: target });
}

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "bubu-fab") {
    openFab(msg.action)
      .then(() => sendResponse({ ok: true }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true;
  }
  if (msg?.type === "bubu-get-prefs") {
    Promise.all([getAppUrl(), getLang()])
      .then(([appUrl, lang]) => sendResponse({ ok: true, appUrl, lang }))
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true;
  }
  if (msg?.type === "bubu-set-lang") {
    const lang = LANGS.includes(msg.lang) ? msg.lang : DEFAULT_LANG;
    chrome.storage.sync.set({ bubu_lang: lang }, () => {
      sendResponse({ ok: true, lang });
    });
    return true;
  }
  if (msg?.type === "bubu-inject-active") {
    chrome.tabs
      .query({ active: true, currentWindow: true })
      .then(async (tabs) => {
        const tab = tabs[0];
        if (!tab?.id || !canInject(tab.url)) {
          sendResponse({ ok: false, error: "此页面无法注入（系统页）" });
          return;
        }
        await injectFab(tab.id);
        try {
          await chrome.tabs.sendMessage(tab.id, { type: "bubu-remount" });
        } catch {
          /* first inject already mounts */
        }
        sendResponse({ ok: true });
      })
      .catch((e) => sendResponse({ ok: false, error: String(e) }));
    return true;
  }
  return false;
});

chrome.tabs.onUpdated.addListener((tabId, info, tab) => {
  if (info.status !== "complete") return;
  if (!canInject(tab.url)) return;
  injectFab(tabId);
});

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  try {
    const tab = await chrome.tabs.get(tabId);
    if (canInject(tab.url)) injectFab(tabId);
  } catch {
    /* ignore */
  }
});

async function registerScripts() {
  try {
    await chrome.scripting.unregisterContentScripts({ ids: ["bubu-fab"] }).catch(() => {});
    await chrome.scripting.registerContentScripts([
      {
        id: "bubu-fab",
        matches: ["http://*/*", "https://*/*"],
        js: ["content.js"],
        runAt: "document_idle",
        persistAcrossSessions: true,
        allFrames: false,
      },
    ]);
  } catch {
    /* older chrome / permission */
  }
}

chrome.runtime.onInstalled.addListener(async () => {
  await getAppUrl(); // migrate localhost → Cloud
  const { bubu_lang } = await chrome.storage.sync.get({ bubu_lang: DEFAULT_LANG });
  if (!LANGS.includes(bubu_lang)) {
    await chrome.storage.sync.set({ bubu_lang: DEFAULT_LANG });
  }
  await registerScripts();
  const tabs = await chrome.tabs.query({});
  for (const tab of tabs) {
    if (tab.id != null && canInject(tab.url)) injectFab(tab.id);
  }
});

chrome.runtime.onStartup.addListener(() => {
  getAppUrl();
  registerScripts();
});
