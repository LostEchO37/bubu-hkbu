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

  const DEFAULT_APP_URL = "https://bubu-hkbu-mdic9zba2hqxaqskyfihkn.streamlit.app";
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

  // Keep the whole fan in the LEFT-UP quadrant (angle ≥ 100°) so nothing clips
  // past the right viewport edge when the orb sits bottom-right.
  const R = 132;
  const deg = (d) => (d * Math.PI) / 180;
  const at = (angleDeg) => ({
    x: Math.round(R * Math.cos(deg(angleDeg))),
    y: Math.round(-R * Math.sin(deg(angleDeg))),
  });

  const ACTION_LAYOUT = [
    { action: "chat", n: "1", ...at(180) },
    { action: "mail", n: "2", ...at(164) },
    { action: "task", n: "3", ...at(148) },
    { action: "tt", n: "4", ...at(132) },
    { action: "plan", n: "5", ...at(116) },
    { action: "lang", n: "文", ...at(100) },
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
  background: rgba(12, 36, 48, 0.22);
  opacity: 0; pointer-events: none;
  transition: opacity 0.15s ease;
}
.wrap.open .scrim { opacity: 1; pointer-events: auto; }
.dock {
  position: fixed;
  right: max(16px, env(safe-area-inset-right));
  bottom: max(20px, env(safe-area-inset-bottom));
  z-index: 2147483646;
  width: 52px; height: 52px;
  pointer-events: none;
}
.orb {
  position: relative; z-index: 2;
  width: 52px; height: 52px; margin: 0; padding: 0;
  border: 0; border-radius: 999px;
  pointer-events: auto; cursor: pointer;
  display: grid; place-items: center;
  color: #0f4a5c;
  font-size: 11px; font-weight: 800;
  background: radial-gradient(circle at 30% 28%, #fff 0%, #e7f6fb 45%, #6ebfd8 100%);
  box-shadow: 0 10px 24px rgba(31,115,140,0.3), 0 0 0 2px rgba(255,255,255,0.7);
  transition: transform 0.18s ease, background 0.18s ease, color 0.18s ease;
  will-change: transform;
}
.orb:hover { transform: scale(1.05); }
.wrap.open .orb {
  background: linear-gradient(145deg, #176f88, #2f9eb8);
  color: #f4fbff;
  transform: rotate(45deg);
}
.orb .x { display: none; font-size: 20px; font-weight: 500; line-height: 1; transform: rotate(-45deg); }
.wrap.open .orb .face { display: none; }
.wrap.open .orb .x { display: block; }
.canvas {
  position: absolute;
  right: 26px;
  bottom: 26px;
  width: 300px;
  height: 300px;
  margin-right: 0;
  pointer-events: none;
  z-index: 1;
  overflow: visible;
  transform: translate(0, 0);
}
.svg { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
.branch {
  stroke: rgba(47,158,184,0.4); stroke-width: 1.5; stroke-linecap: round; fill: none;
  opacity: 0;
}
.wrap.open .branch { opacity: 1; transition: opacity 0.15s ease var(--d,0s); }
.sat {
  position: absolute; left: 50%; top: 50%;
  width: 54px; height: 54px; padding: 3px; border-radius: 999px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
  border: 0;
  background: #fff;
  box-shadow: 0 8px 18px rgba(36,110,130,0.18), 0 0 0 1.5px rgba(255,255,255,0.95);
  color: #164858; cursor: pointer;
  opacity: 0; pointer-events: none;
  transform: translate(-50%,-50%) scale(0.35);
  transition: transform 0.22s cubic-bezier(.22,.9,.28,1) var(--d,0s),
    opacity 0.16s ease var(--d,0s);
  font: inherit;
  will-change: transform, opacity;
}
.wrap.open .sat {
  opacity: 1; pointer-events: auto;
  transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) scale(1);
}
.sat:hover {
  box-shadow: 0 10px 22px rgba(36,110,130,0.28), 0 0 0 2px #7ec8e3;
}
.sat.lang-sat { background: #dff3f9; color: #145a70; }
.num { font-size: 9px; font-weight: 800; color: #2f9eb8; line-height: 1; }
.lab { font-size: 11px; font-weight: 750; line-height: 1.05; text-align: center; max-width: 48px; }
@media (prefers-reduced-motion: reduce) {
  .orb, .sat, .branch, .scrim { transition: none !important; }
}
`;

  let currentLang = "zh-CN";

  function t(key) {
    return (I18N[currentLang] || I18N["zh-CN"])[key] || key;
  }

  function actionLabel(action) {
    return action === "lang" ? t("lang") : t(action);
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
    // Close menu immediately so the page feels responsive before navigation.
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

    // Canvas origin = orb center; positions are relative so left-up sats stay on-screen.
    const canvas = document.createElement("div");
    canvas.className = "canvas";

    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("class", "svg");
    svg.setAttribute("viewBox", "0 0 300 300");
    svg.setAttribute("aria-hidden", "true");

    const origin = 150; // canvas center == orb center via CSS anchoring
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
      const delay = `${0.02 + i * 0.03}s`;
      const line = document.createElementNS(svgNS, "line");
      line.setAttribute("class", "branch");
      line.setAttribute("x1", String(origin));
      line.setAttribute("y1", String(origin));
      line.setAttribute("x2", String(origin + item.x));
      line.setAttribute("y2", String(origin + item.y));
      line.style.setProperty("--d", delay);
      svg.appendChild(line);

      const sat = document.createElement("button");
      sat.type = "button";
      sat.className = item.action === "lang" ? "sat lang-sat" : "sat";
      // Anchor sats at canvas center (orb), then offset by item.x/y (always ≤0 in x).
      sat.style.left = `${origin}px`;
      sat.style.top = `${origin}px`;
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

    dock.appendChild(canvas);
    dock.appendChild(orb);
    wrap.appendChild(scrim);
    wrap.appendChild(dock);
    shadow.appendChild(style);
    shadow.appendChild(wrap);
    (document.documentElement || document.body).appendChild(host);

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

  let authTimer = null;
  const scheduleAuthSync = () => {
    if (authTimer) return;
    authTimer = setTimeout(() => {
      authTimer = null;
      syncAuthFromUrl();
    }, 10000);
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
