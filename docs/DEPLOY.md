# Deploy on Streamlit Community Cloud

## Live URL

- Preferred short (if you renamed it and Sharing is Public): https://bubu-hkbu.streamlit.app/
- Legacy hash URL (may 404 after rename/delete): `https://bubu-hkbu-*.streamlit.app/`
- Repo: https://github.com/LostEchO37/bubu-hkbu (`main` / `app.py`)

After any rename, reboot, or “not found” page, open [share.streamlit.io](https://share.streamlit.io/) → **My apps** and copy the URL shown on the app card — that is the source of truth. Update the browser-extension default if it changed.

## Checklist

1. Deploy from the public GitHub repo (`LostEchO37/bubu-hkbu`).
2. Set **Python 3.12** in app Settings (matches `runtime.txt`).
3. Paste Secrets (see `.streamlit/secrets.toml.example`):
   - `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_VISION_MODEL`
   - `LLM_PROVIDER`, `HKBU_SESSION_SECRET` (long random string)
4. Sharing → **Public** (Private shows “You do not have access… / not found” for most visitors).
5. Optional: rename App URL to `bubu-hkbu` for a shorter link, then reboot once.
6. After deploy, hard-refresh once (Ctrl/⌘+Shift+R) if widgets show “Failed to fetch dynamically imported module”. The app also auto soft-reloads once on that error.
7. Keep a sensible `streamlit` range in `requirements.txt` so Cloud rebuilds stay predictable.
8. Reboot the app from Cloud “Manage app” if chunk errors persist after refresh.

## Other devices feel stuck / never finish loading

Common causes on phones / campus Wi‑Fi:

1. **Cloud sleep** — after ~12h without traffic the app hibernates. Visitors see a wake page; click **Yes, get this app back up** and wait **30–60s**, then hard-refresh.
2. **Sharing not Public** — other accounts get “not found / no access”.
3. **Stale JS chunks after redeploy / sleep** — hard-refresh (Ctrl/⌘+Shift+R) once. The app also auto soft-reloads once when it detects `Failed to fetch dynamically imported module` (typical chat_input / uploader failure).
4. **Too many widgets on first paint** — fixed in v1.0.1: workspace uploaders/inputs stay unmounted until the user opens 「我的资料」.

Optional: GitHub Action `.github/workflows/keep-awake.yml` pings the live URL on a schedule (best-effort; Cloud may still sleep).

If chat_input still errors after deploy: Cloud **Manage app → Reboot**, then open the app in a private window once.

## “You do not have access to this app or it does not exist”

1. Confirm you are signed into Streamlit as the same GitHub user that owns the deploy (`lostecho37`).
2. Open **My apps** — if the card is missing, **Create app** again from `LostEchO37/bubu-hkbu` / `main` / `app.py`.
3. App ⋮ → **Settings** → **Sharing = Public**.
4. ⋮ → **Reboot**. Wait until status is running, then open the URL from the app card (not an old bookmarked hash).
5. Paste that URL into the floating-orb extension options.

## Storage caveat

SQLite under `data/users.db` is **local to the Cloud container**. Reboot, sleep, or rebuild may wipe accounts and timetables. The UI shows a notice on Cloud. For durable sync, move to an external DB later.
