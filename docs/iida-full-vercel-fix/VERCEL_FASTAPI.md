# Deploy FastAPI backend on Vercel

## Error: `app.py does not define a top-level "app" FastAPI instance`

Vercel scans for `app.py` first. In this monorepo the Streamlit legacy UI lives in
`streamlit_app.py`; the production API is **`backend_api.py`** (or `backend/main.py`).

### Fix

`pyproject.toml` must point at the real API:

```toml
[tool.vercel]
entrypoint = "backend_api:app"
```

This branch (`NEW-IIDA`) includes:

- `backend_api.py` — re-exports `backend.main:app`
- `pyproject.toml` — explicit Vercel entrypoint
- `vercel.json` — function limits for `backend_api.py`
- `requirements.txt` — installs `requirements-api.txt`

### Vercel project settings

1. **Root Directory:** leave empty (repo root)
2. **Production Branch:** `NEW-IIDA` or `main` after merge
3. **Environment variables:** see `.env.example` (`JWT_SECRET`, `DATABASE_URL`, `PERPLEXITY_API_KEY`, …)

### If your repo is still named `iida-full`

Either reconnect Vercel to **`vidhu-ops/iida-final-vercel`** branch **`NEW-IIDA`**, or copy these four files into `iida-full` and push.
