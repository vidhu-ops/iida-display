# Fix for `iida-full` Vercel build error

Copy these files to the **root** of `vidhu-ops/iida-full` (branch `NEW-IIDA`) and push.

## The error

```
Error: Found app.py but it does not define a top-level "app" FastAPI instance.
```

Vercel finds `app.py` (Streamlit) but your API is in **`backend_api.py`**.

## The fix (one file minimum)

Add **`pyproject.toml`** at repo root:

```toml
[tool.vercel]
entrypoint = "backend_api:app"
```

Do **not** use `_apply_research_patch:app` — that is a dev patch script.

## Full fix (recommended)

Copy everything from this folder to your `iida-full` repo root:

| File | Purpose |
|------|---------|
| `pyproject.toml` | Tells Vercel to use `backend_api:app` |
| `backend_api.py` | Only needed if your repo lacks it; re-exports `backend.main:app` |
| `vercel.json` | Function config for `backend_api.py` |
| `requirements.txt` | Python deps for Vercel |
| `vercelignore.example` | Rename to `.vercelignore` if deploying API only |

Then commit, push, redeploy.

## If `iida-full` is private

Reconnect Vercel to **`vidhu-ops/iida-final-vercel`** branch **`NEW-IIDA`** after merging this fix there, or paste the files manually in GitHub web UI.

## Vercel Agent prompt

```
Fix FastAPI entrypoint for iida-full branch NEW-IIDA.
Add pyproject.toml with entrypoint = "backend_api:app".
Ensure backend_api.py exports FastAPI app. Redeploy production.
Do not use _apply_research_patch as entrypoint.
```
