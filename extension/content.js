(() => {
  if (window.__bubuFabInstalled) return;
  window.__bubuFabInstalled = true;

  // Never mount on Streamlit Cloud — avoids fighting app JS chunks / Manage bar.
  try {
    const h = location.hostname || "";
    if (h === "streamlit.app" || h.endsWith(".streamlit.app")) {
      return;
    }
  } catch {
    /* continue */
  }

  const DEFAULT_APP_URL = "https://bubu-hkbu.streamlit.app";
  const LANGS = ["zh-CN", "zh-TW", "en"];
  const I18N = {
    "zh-CN": {
      orb: "阿Bu",
      chat: "开聊",
      mail: "回信",
      task: "任务",
      tt: "课表",
      plan: "计划",
      lang: "语言",
      langHint: "切换语言",
    },
    "zh-TW": {
      orb: "阿Bu",
      chat: "開聊",
      mail: "回信",
      task: "任務",
      tt: "課表",
      plan: "計劃",
      lang: "語言",
      langHint: "切換語言",
    },
    en: {
      orb: "BuBu",
      chat: "Chat",
      mail: "Mail",
      task: "Tasks",
      tt: "Table",
      plan: "Plan",
      lang: "Lang",
      langHint: "Switch language",
    },
  };
  const LANG_BADGE = { "zh-CN": "简", "zh-TW": "繁", en: "EN" };

  const R = 148;
  const deg = (d) => (d * Math.PI) / 180;
  const at = (angleDeg) => ({
    x: Math.round(R * Math.cos(deg(angleDeg))),
    y: Math.round(-R * Math.sin(deg(angleDeg))),
  });

  // Arc stays upper-left so nothing clips under the orb / browser chrome.
  const ACTION_LAYOUT = [
    { action: "chat", n: "1", ...at(175) },
    { action: "mail", n: "2", ...at(150) },
    { action: "task", n: "3", ...at(125) },
    { action: "tt", n: "4", ...at(100) },
    { action: "plan", n: "5", ...at(75) },
    { action: "lang", n: "文", ...at(50) },
  ];

  const CSS = `
:host, * { box-sizing: border-box; }
.wrap {
  all: initial;
  font-family: "Noto Sans SC", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", system-ui, sans-serif;
  -webkit-tap-highlight-color: transparent;
}
.scrim {
  position: fixed; inset: 0; z-index: 2147483645;
  background: rgba(15, 40, 52, 0.18);
  opacity: 0; pointer-events: none;
  backdrop-filter: blur(2px);
  transition: opacity 0.22s ease;
}
.wrap.open .scrim { opacity: 1; pointer-events: auto; }
.dock {
  position: fixed;
  right: max(14px, env(safe-area-inset-right));
  bottom: max(22px, env(safe-area-inset-bottom));
  z-index: 2147483646;
  width: 56px; height: 56px;
  pointer-events: none;
}
.orb {
  position: relative; z-index: 2;
  width: 56px; height: 56px; margin: 0; padding: 0;
  border: 0; border-radius: 999px;
  pointer-events: auto; cursor: pointer;
  display: grid; place-items: center;
  color: #0f4a5c;
  font-size: 11px; font-weight: 800; letter-spacing: -0.02em;
  background:
    radial-gradient(circle at 30% 28%, #ffffff 0%, #e7f6fb 42%, #6ebfd8 100%);
  box-shadow:
    0 12px 28px rgba(31, 115, 140, 0.34),
    0 0 0 3px rgba(255,255,255,0.65),
    inset 0 1px 0 rgba(255,255,255,0.9);
  transition: transform 0.28s cubic-bezier(.22,.9,.28,1), box-shadow 0.28s ease, background 0.28s ease, color 0.28s ease;
}
.orb:hover { transform: scale(1.06); }
.wrap.open .orb {
  background: linear-gradient(145deg, #176f88, #2f9eb8);
  color: #f4fbff;
  transform: rotate(45deg) scale(1.04);
  box-shadow: 0 14px 32px rgba(31, 115, 140, 0.42), 0 0 0 3px rgba(255,255,255,0.35);
}
.orb .face { line-height: 1; transform: translateY(1px); }
.orb .x { display: none; font-size: 22px; font-weight: 500; line-height: 1; transform: rotate(-45deg); }
.wrap.open .orb .face { display: none; }
.wrap.open .orb .x { display: block; }
.canvas {
  position: absolute; right: 50%; bottom: 50%;
  width: 380px; height: 380px;
  transform: translate(50%, 50%);
  pointer-events: none; z-index: 1;
  overflow: visible;
}
.svg { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
.branch {
  stroke: rgba(47,158,184,0.42); stroke-width: 1.75; stroke-linecap: round; fill: none;
  opacity: 0; stroke-dasharray: 200; stroke-dashoffset: 200;
}
.wrap.open .branch {
  opacity: 1;
  animation: draw 0.48s cubic-bezier(.22,.9,.28,1) var(--d,0s) both;
}
.sat {
  position: absolute; left: 50%; top: 50%;
  width: 58px; height: 58px; padding: 4px; border-radius: 999px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 2px;
  border: 0;
  background: linear-gradient(165deg, #ffffff, #eaf6fb);
  box-shadow:
    0 10px 24px rgba(36,110,130,0.2),
    0 0 0 2px rgba(255,255,255,0.95);
  color: #164858; cursor: pointer;
  opacity: 0; pointer-events: none;
  transform: translate(-50%,-50%) scale(0.18);
  transition: transform 0.4s cubic-bezier(.22,.9,.28,1) var(--d,0s),
    opacity 0.26s ease var(--d,0s), box-shadow 0.2s ease;
  font: inherit;
}
.wrap.open .sat {
  opacity: 1; pointer-events: auto;
  transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) scale(1);
}
.sat:hover {
  box-shadow: 0 14px 30px rgba(36,110,130,0.3), 0 0 0 2px #7ec8e3;
  transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) scale(1.06);
}
.sat.lang-sat {
  background: linear-gradient(165deg, #dff3f9, #b9e3f0);
  color: #145a70;
}
.num { font-size: 9px; font-weight: 800; color: #2f9eb8; line-height: 1; letter-spacing: 0.02em; }
.lab { font-size: 11px; font-weight: 750; line-height: 1.05; text-align: center; max-width: 52px; }
@keyframes draw {
  from { stroke-dashoffset: 200; opacity: 0; }
  to { stroke-dashoffset: 0; opacity: 1; }
}
@media (prefers-reduced-motion: reduce) {
  .orb, .sat, .branch, .scrim { transition: none !important; animation: none !important; }
}
`;

  let currentLang = "zh-CN";

  function t(key) {
    return (I18N[currentLang] || I18N["zh-CN"])[key] || key;
  }

  function actionLabel(action) {
    if (action === "lang") return t("lang");
    return t(action);
  }

  function syncAuthFromUrl() {
    try {
      const auth = new URLSearchParams(location.search).get("auth");
      if (!auth) return;
      chrome.storage.sync.get({ bubu_app_url: DEFAULT_APP_URL }, (data) => {
        try {
          let raw = String(data.bubu_app_url || DEFAULT_APP_URL);
          if (/localhost|127\.0\.0\.1/i.test(raw)) raw = DEFAULT_APP_URL;
          const app = new URL(raw);
          if (location.origin === app.origin) {
            chrome.storage.local.set({ bubu_auth: auth });
          }
        } catch {
          /* ignore */
        }
      });
    } catch {
      /* ignore */
    }
  }

  function go(action) {
    chrome.runtime.sendMessage({ type: "bubu-fab", action }, () => {
      void chrome.runtime.lastError;
    });
  }

  function cycleLang(applyUi) {
    const i = LANGS.indexOf(currentLang);
    const next = LANGS[(i + 1) % LANGS.length];
    chrome.runtime.sendMessage({ type: "bubu-set-lang", lang: next }, (res) => {
      void chrome.runtime.lastError;
      currentLang = res?.lang || next;
      applyUi();
    });
  }

  function loadLang(cb) {
    chrome.storage.sync.get({ bubu_lang: "zh-CN" }, (data) => {
      currentLang = LANGS.includes(data.bubu_lang) ? data.bubu_lang : "zh-CN";
      cb();
    });
  }

  function mount() {
    if (document.getElementById("bubu-fab-host")) return;

    const host = document.createElement("div");
    host.id = "bubu-fab-host";
    host.style.cssText =
      "all:initial;position:fixed;z-index:2147483646;inset:auto 0 0 auto;width:0;height:0;overflow:visible;pointer-events:none;";

    const shadow = host.attachShadow({ mode: "open" });
    const style = document.createElement("style");
    style.textContent = CSS;

    const wrap = document.createElement("div");
    wrap.className = "wrap";

    const scrim = document.createElement("div");
    scrim.className = "scrim";
    scrim.addEventListener("click", () => wrap.classList.remove("open"));

    const dock = document.createElement("div");
    dock.className = "dock";

    const orb = document.createElement("button");
    orb.type = "button";
    orb.className = "orb";
    orb.innerHTML =
      '<span class="face">(^o^)</span><span class="x" aria-hidden="true">×</span>';

    const canvas = document.createElement("div");
    canvas.className = "canvas";

    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("class", "svg");
    svg.setAttribute("viewBox", "0 0 380 380");
    svg.setAttribute("aria-hidden", "true");

    const satButtons = [];

    function applyLabels() {
      orb.setAttribute("aria-label", t("orb"));
      satButtons.forEach(({ el, action, n }) => {
        const label = actionLabel(action);
        el.setAttribute("aria-label", action === "lang" ? t("langHint") : label);
        const num = action === "lang" ? LANG_BADGE[currentLang] || "文" : n;
        el.innerHTML = `<span class="num">${num}</span><span class="lab">${label}</span>`;
      });
    }

    ACTION_LAYOUT.forEach((item, i) => {
      const delay = `${0.02 + i * 0.04}s`;
      const line = document.createElementNS(svgNS, "line");
      line.setAttribute("class", "branch");
      line.setAttribute("x1", "190");
      line.setAttribute("y1", "190");
      line.setAttribute("x2", String(190 + item.x));
      line.setAttribute("y2", String(190 + item.y));
      line.style.setProperty("--d", delay);
      svg.appendChild(line);

      const sat = document.createElement("button");
      sat.type = "button";
      sat.className = item.action === "lang" ? "sat lang-sat" : "sat";
      sat.style.setProperty("--x", `${item.x}px`);
      sat.style.setProperty("--y", `${item.y}px`);
      sat.style.setProperty("--d", delay);
      sat.addEventListener("click", (e) => {
        e.stopPropagation();
        if (item.action === "lang") {
          cycleLang(applyLabels);
          return;
        }
        wrap.classList.remove("open");
        go(item.action);
      });
      canvas.appendChild(sat);
      satButtons.push({ el: sat, action: item.action, n: item.n });
    });

    canvas.insertBefore(svg, canvas.firstChild);
    orb.addEventListener("click", (e) => {
      e.stopPropagation();
      wrap.classList.toggle("open");
    });

    applyLabels();

    dock.appendChild(orb);
    dock.appendChild(canvas);
    wrap.appendChild(scrim);
    wrap.appendChild(dock);
    shadow.appendChild(style);
    shadow.appendChild(wrap);

    const parent = document.documentElement || document.body;
    parent.appendChild(host);

    chrome.storage.onChanged.addListener((changes, area) => {
      if (area !== "sync" || !changes.bubu_lang) return;
      const next = changes.bubu_lang.newValue;
      if (LANGS.includes(next)) {
        currentLang = next;
        applyLabels();
      }
    });
  }

  function boot() {
    syncAuthFromUrl();
    loadLang(() => mount());
  }

  if (document.documentElement) boot();
  else document.addEventListener("DOMContentLoaded", boot, { once: true });

  // Auth sync only when URL may carry token; keep rare to avoid jank.
  let authTicks = null;
  const scheduleAuthSync = () => {
    if (authTimer) return;
    authTimer = setTimeout(() => {
      authTimer = null;
      syncAuthFromUrl();
    }, 8000);
  };
  window.addEventListener("popstate", scheduleAuthSync, { passive: true });
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) scheduleAuthSync();
  });

  chrome.runtime.onMessage.addListener((msg) => {
    if (msg?.type === "bubu-remount") {
      window.__bubuFabInstalled = false;
      document.getElementById("bubu-fab-host")?.remove();
      window.__bubuFabInstalled = true;
      boot();
    }
  });
})();
