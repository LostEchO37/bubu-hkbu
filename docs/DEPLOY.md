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
4. Sharing → **Public** and turn **OFF** any “Require login / authentication” for viewers.
   - If Sharing is private, phones/other accounts get stuck in a **303 login redirect loop** (`share.streamlit.io/-/auth/app`) that looks like an endless spinner.
   - Verify in an **incognito** window while logged out of Streamlit: the app must open without asking you to sign in to Streamlit.
5. Optional: rename App URL to `bubu-hkbu` for a shorter link, then reboot once.
6. After deploy, hard-refresh once (Ctrl/⌘+Shift+R) if widgets show “Failed to fetch dynamically imported module”. The app also auto soft-reloads once on that error.
7. Keep a sensible `streamlit` range in `requirements.txt` so Cloud rebuilds stay predictable.
8. Reboot the app from Cloud “Manage app” if chunk errors persist after refresh.

## Other devices feel stuck / never finish loading

Sharing **Public** is required, but Public alone does not prevent spinners. Observed on Cloud:

1. **Cold connect** — first open after idle can sit on Streamlit’s spinner **30–90s** while the app iframe boots. Wait; if still blank after ~2 minutes: **Manage app → Reboot**.
2. **Backend hung** — `/~/+/_stcore/health` should return `ok`. If it times out, Reboot (not a Sharing issue).
3. **Blank skeleton inputs** — too many widgets on first paint starve JS chunks. v1.0.3 keeps login minimal (settings closed; login/register not both mounted).
4. **Stale chunks after redeploy** — hard-refresh (Ctrl/⌘+Shift+R). App auto soft-reloads once on `Failed to fetch dynamically imported module`.

Optional: GitHub Action `.github/workflows/keep-awake.yml` pings the live URL on a schedule (best-effort).

## “You do not have access to this app or it does not exist”

1. Confirm you are signed into Streamlit as the same GitHub user that owns the deploy (`lostecho37`).
2. Open **My apps** — if the card is missing, **Create app** again from `LostEchO37/bubu-hkbu` / `main` / `app.py`.
3. App ⋮ → **Settings** → **Sharing = Public**.
4. ⋮ → **Reboot**. Wait until status is running, then open the URL from the app card (not an old bookmarked hash).
5. Paste that URL into the floating-orb extension options.

## Storage caveat

SQLite under `data/users.db` is **local to the Cloud container**. Reboot, sleep, or rebuild may wipe accounts and timetables. The UI shows a notice on Cloud. For durable sync, move to an external DB later.
