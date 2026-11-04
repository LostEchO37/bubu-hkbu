// Short public URL after Cloud rename. Old hash URLs 404 with "no access / does not exist".
const DEFAULT_APP_URL = "https://bubu-hkbu.streamlit.app";
const DEFAULT_LANG = "zh-CN";
const LANGS = ["zh-CN", "zh-TW", "en"];

function normalizeAppUrl(raw) {
  let s = String(raw || "").trim().replace(/\/$/, "");
  if (!s || /localhost|127\.0\.0\.1/i.test(s)) return DEFAULT_APP_URL;
  try {
    const u = new URL(s);
    // Retired hash subdomain after rename — force the current short name.
    if (/^bubu-hkbu-[a-z0-9]+\.streamlit\.app$/i.test(u.hostname)) {
      return DEFAULT_APP_URL;
    }
    if (u.hostname === "streamlit.app") return DEFAULT_APP_URL;
  } catch {
    return DEFAULT_APP_URL;
  }
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

function isStreamlitHost(url) {
  try {
    const h = new URL(url).hostname;
    return h === "streamlit.app" || h.endsWith(".streamlit.app");
  } catch {
    return false;
  }
}

/** Never inject on Streamlit Cloud — FAB lives on other sites and deep-links in. */
async function injectFab(tabId, tabUrl) {
  try {
    if (tabUrl && isStreamlitHost(tabUrl)) return;
    const [{ result: already }] = await chrome.scripting.executeScript({
      target: { tabId },
      func: () =>
        !!(
          window.__bubuFabInstalled ||
          document.getElementById("bubu-fab-host")
        ),
    });
    if (already) return;
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

function waitTabComplete(tabId, timeoutMs = 60000) {
  return new Promise((resolve) => {
    let done = false;
    const finish = (ok) => {
      if (done) return;
      done = true;
      clearTimeout(timer);
      chrome.tabs.onUpdated.removeListener(listener);
      resolve(ok);
    };
    const timer = setTimeout(() => finish(false), timeoutMs);
    function listener(id, info) {
      if (id === tabId && info.status === "complete") finish(true);
    }
    chrome.tabs.onUpdated.addListener(listener);
    chrome.tabs.get(tabId).then((tab) => {
      if (tab.status === "complete") finish(true);
    }).catch(() => finish(false));
  });
}

async function openFab(action) {
  const base = await getAppUrl();
  const lang = await getLang();
  const warm = new URL(base);
  const url = new URL(base);
  const auth = await resolveAuth(url.origin);
  if (auth) url.searchParams.set("auth", auth);
  if (lang && lang !== "zh-CN") url.searchParams.set("lang", lang);

  if (action === "chat") {
    url.searchParams.set("wake", "1");
  } else if (action) {
    url.searchParams.set("fab", action);
  }

  const target = url.toString();
  const warmUrl = warm.toString();
  const tabs = await chrome.tabs.query({});
  const hit = tabs.find((t) => {
    try {
      return new URL(t.url || "").origin === url.origin;
    } catch {
      return false;
    }
  });

  // Reuse a warm Cloud tab when possible (avoids cold auth handshake + spinner).
  if (hit?.id != null) {
    await chrome.tabs.update(hit.id, { url: target, active: true });
    if (hit.windowId != null) {
      try {
        await chrome.windows.update(hit.windowId, { focused: true });
      } catch {
        /* ignore */
      }
    }
    return;
  }

  // Cold start: open clean app URL first so Cloud can finish cookie/auth, then deep-link.
  const tab = await chrome.tabs.create({ url: warmUrl, active: true });
  if (tab?.id == null) return;
  await waitTabComplete(tab.id, 60000);
  // Small beat for Streamlit websocket after document complete.
  await new Promise((r) => setTimeout(r, 1200));
  try {
    await chrome.tabs.update(tab.id, { url: target, active: true });
  } catch {
    /* tab closed */
  }
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
        try {
          await chrome.scripting.executeScript({
            target: { tabId: tab.id },
            func: () => {
              window.__bubuFabInstalled = false;
              document.getElementById("bubu-fab-host")?.remove();
            },
          });
        } catch {
          /* ignore */
        }
        await injectFab(tab.id, tab.url);
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

const _injectSoon = new Map();
function scheduleInject(tabId, tabUrl) {
  if (!canInject(tabUrl)) return;
  if (isStreamlitHost(tabUrl)) return;
  const prev = _injectSoon.get(tabId);
  if (prev) clearTimeout(prev);
  _injectSoon.set(
    tabId,
    setTimeout(() => {
      _injectSoon.delete(tabId);
      injectFab(tabId, tabUrl);
    }, 350)
  );
}

chrome.tabs.onUpdated.addListener((tabId, info, tab) => {
  if (info.status !== "complete") return;
  scheduleInject(tabId, tab.url);
});

chrome.tabs.onActivated.addListener(async ({ tabId }) => {
  try {
    const tab = await chrome.tabs.get(tabId);
    scheduleInject(tabId, tab.url);
  } catch {
    /* ignore */
  }
});

chrome.runtime.onInstalled.addListener(async () => {
  await getAppUrl();
  const { bubu_lang } = await chrome.storage.sync.get({ bubu_lang: DEFAULT_LANG });
  if (!LANGS.includes(bubu_lang)) {
    await chrome.storage.sync.set({ bubu_lang: DEFAULT_LANG });
  }
});
