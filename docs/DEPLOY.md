# Deploy on Streamlit Community Cloud

## Live URL

- Current: https://bubu-hkbu-mdic9zba2hqxaqskyfihkn.streamlit.app/
- Repo: https://github.com/LostEchO37/bubu-hkbu (`main` / `app.py`)

## Checklist

1. Deploy from the public GitHub repo (`LostEchO37/bubu-hkbu`).
2. Set **Python 3.12** in app Settings (matches `runtime.txt`).
3. Paste Secrets (see `.streamlit/secrets.toml.example`):
   - `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_MODEL`, `OPENAI_VISION_MODEL`
   - `LLM_PROVIDER`, `HKBU_SESSION_SECRET` (long random string)
4. Sharing → **Public**.
5. Optional: rename App URL to `bubu-hkbu` for a shorter link.
6. After deploy, hard-refresh once (Ctrl/⌘+Shift+R) if widgets show “Failed to fetch dynamically imported module”. The app also auto soft-reloads once on that error.
7. Pin `streamlit==…` in `requirements.txt` so Cloud does not silently upgrade and bust JS chunk hashes mid-session.
8. Reboot the app from Cloud “Manage app” if chunk errors persist after refresh.

## Storage caveat

SQLite under `data/users.db` is **local to the Cloud container**. Reboot, sleep, or rebuild may wipe accounts and timetables. The UI shows a notice on Cloud. For durable sync, move to an external DB later.
