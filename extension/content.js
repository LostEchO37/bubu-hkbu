(() => {
  if (window.__bubuFabInstalled) return;
  window.__bubuFabInstalled = true;

  const DEFAULT_APP_URL = "https://bubu-hkbu.streamlit.app";
  const LANGS = ["zh-CN", "zh-TW", "en"];
  const I18N = {
    "zh-CN": {
      orb: "阿Bu 功能球",
      chat: "开聊",
      mail: "回信",
      task: "任务",
      tt: "课表",
      plan: "计划",
      lang: "语言",
      langHint: "切换语言",
    },
    "zh-TW": {
      orb: "阿Bu 功能球",
      chat: "開聊",
      mail: "回信",
      task: "任務",
      tt: "課表",
      plan: "計劃",
      lang: "語言",
      langHint: "切換語言",
    },
    en: {
      orb: "BuBu menu",
      chat: "Chat",
      mail: "Mail",
      task: "Tasks",
      tt: "Timetable",
      plan: "Plan",
      lang: "Lang",
      langHint: "Switch language",
    },
  };
  const LANG_BADGE = { "zh-CN": "简", "zh-TW": "繁", en: "EN" };

  const R = 158;
  const deg = (d) => (d * Math.PI) / 180;
  const at = (angleDeg) => ({
    x: Math.round(R * Math.cos(deg(angleDeg))),
    y: Math.round(-R * Math.sin(deg(angleDeg))),
  });

  const ACTION_LAYOUT = [
    { action: "chat", n: "1", ...at(180) },
    { action: "mail", n: "2", ...at(157.5) },
    { action: "task", n: "3", ...at(135) },
    { action: "tt", n: "4", ...at(112.5) },
    { action: "plan", n: "5", ...at(90) },
    { action: "lang", n: "文", ...at(67.5) },
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
  background: rgba(20, 55, 68, 0.16);
  opacity: 0; pointer-events: none;
  transition: opacity 0.2s ease;
}
.wrap.open .scrim { opacity: 1; pointer-events: auto; }
.dock {
  position: fixed;
  right: max(12px, env(safe-area-inset-right));
  bottom: max(16px, env(safe-area-inset-bottom));
  z-index: 2147483646;
  width: 48px; height: 48px;
  pointer-events: none;
}
.orb {
  position: relative; z-index: 2;
  width: 48px; height: 48px; margin: 0; padding: 0;
  border: 1px solid rgba(255,255,255,0.85); border-radius: 999px;
  pointer-events: auto; cursor: pointer;
  display: grid; place-items: center;
  color: #145066; font-size: 10px; font-weight: 800;
  background: radial-gradient(circle at 32% 28%, #fff 0%, #d7f0f8 48%, #7ec4d8 100%);
  box-shadow: 0 10px 28px rgba(31,115,140,0.32), inset 0 1px 0 rgba(255,255,255,0.75);
  transition: transform 0.25s ease, background 0.25s ease, color 0.25s ease;
}
.orb:hover { transform: scale(1.05); }
.wrap.open .orb {
  background: linear-gradient(145deg, #1a6f88, #2f9eb8);
  color: #f4fbff; transform: rotate(90deg) scale(1.02);
}
.orb .x { display: none; font-size: 20px; font-weight: 500; line-height: 1; }
.wrap.open .orb .face { display: none; }
.wrap.open .orb .x { display: block; }
.lang-chip {
  position: absolute; right: 50px; bottom: 4px; z-index: 3;
  pointer-events: auto; cursor: pointer;
  min-width: 28px; height: 22px; padding: 0 6px;
  border-radius: 999px; border: 1px solid rgba(255,255,255,0.9);
  background: rgba(255,255,255,0.95); color: #1f738c;
  font-size: 11px; font-weight: 800; line-height: 22px; text-align: center;
  box-shadow: 0 6px 16px rgba(31,115,140,0.22);
}
.canvas {
  position: absolute; right: 50%; bottom: 50%;
  width: 400px; height: 400px;
  transform: translate(50%, 50%);
  pointer-events: none; z-index: 1;
}
.svg { position: absolute; inset: 0; width: 100%; height: 100%; overflow: visible; }
.branch {
  stroke: rgba(47,158,184,0.45); stroke-width: 2; stroke-linecap: round; fill: none;
  opacity: 0; stroke-dasharray: 220; stroke-dashoffset: 220;
}
.wrap.open .branch {
  opacity: 1;
  animation: draw 0.5s cubic-bezier(.22,.9,.28,1) var(--d,0s) both;
}
.sat {
  position: absolute; left: 50%; top: 50%;
  width: 56px; height: 56px; padding: 4px; border-radius: 999px;
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 1px;
  border: 1px solid rgba(255,255,255,0.9);
  background: linear-gradient(160deg, rgba(255,255,255,0.98), rgba(220,240,248,0.95));
  box-shadow: 0 8px 22px rgba(36,110,130,0.2);
  color: #164858; cursor: pointer;
  opacity: 0; pointer-events: none;
  transform: translate(-50%,-50%) scale(0.2);
  transition: transform 0.42s cubic-bezier(.22,.9,.28,1) var(--d,0s),
    opacity 0.28s ease var(--d,0s);
  font: inherit;
}
.wrap.open .sat {
  opacity: 1; pointer-events: auto;
  transform: translate(calc(-50% + var(--x)), calc(-50% + var(--y))) scale(1);
}
.sat:hover { box-shadow: 0 12px 28px rgba(36,110,130,0.32); }
.sat.lang-sat {
  background: linear-gradient(160deg, #e8f7fb, #cfeaf3);
  color: #1f738c;
}
.num { font-size: 9px; font-weight: 800; color: #2f9eb8; line-height: 1; }
.lab { font-size: 12px; font-weight: 700; line-height: 1.1; text-align: center; }
@keyframes draw {
  from { stroke-dashoffset: 220; opacity: 0; }
  to { stroke-dashoffset: 0; opacity: 1; }
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

    const langChip = document.createElement("button");
    langChip.type = "button";
    langChip.className = "lang-chip";
    langChip.title = t("langHint");

    const canvas = document.createElement("div");
    canvas.className = "canvas";

    const svgNS = "http://www.w3.org/2000/svg";
    const svg = document.createElementNS(svgNS, "svg");
    svg.setAttribute("class", "svg");
    svg.setAttribute("viewBox", "0 0 400 400");
    svg.setAttribute("aria-hidden", "true");

    const satButtons = [];

    function applyLabels() {
      orb.setAttribute("aria-label", t("orb"));
      langChip.textContent = LANG_BADGE[currentLang] || "简";
      langChip.title = t("langHint");
      satButtons.forEach(({ el, action, n }) => {
        const label = actionLabel(action);
        el.setAttribute("aria-label", label);
        const num = action === "lang" ? LANG_BADGE[currentLang] || "文" : n;
        el.innerHTML = `<span class="num">${num}</span><span class="lab">${label}</span>`;
      });
    }

    ACTION_LAYOUT.forEach((item, i) => {
      const delay = `${0.03 + i * 0.045}s`;
      const line = document.createElementNS(svgNS, "line");
      line.setAttribute("class", "branch");
      line.setAttribute("x1", "200");
      line.setAttribute("y1", "200");
      line.setAttribute("x2", String(200 + item.x));
      line.setAttribute("y2", String(200 + item.y));
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
    langChip.addEventListener("click", (e) => {
      e.stopPropagation();
      cycleLang(applyLabels);
    });

    applyLabels();

    dock.appendChild(orb);
    dock.appendChild(langChip);
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

  // Slow auth sync — avoid competing with Streamlit chunk downloads on Cloud.
  setInterval(syncAuthFromUrl, 12000);
  chrome.runtime.onMessage.addListener((msg) => {
    if (msg?.type === "bubu-remount") {
      window.__bubuFabInstalled = false;
      document.getElementById("bubu-fab-host")?.remove();
      window.__bubuFabInstalled = true;
      boot();
    }
  });
})();
