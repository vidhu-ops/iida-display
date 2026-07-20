# IIDA Display

Flask web app for business intelligence, planning, mentor chat, and payments. Originally built on Replit; configured for **Vercel** deployment with a **Neon PostgreSQL** database.

## Stack

- Python 3.11 + Flask
- SQLAlchemy + PostgreSQL (Neon)
- Google Gemini for AI reports
- Cashfree for payments (optional)

## Local development

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python main.py
```

Open http://localhost:5000

## Environment variables

Copy `.env.example` to `.env` and set:

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes (prod) | Neon PostgreSQL connection string |
| `SESSION_SECRET` | Yes | Flask session signing key |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `CASHFREE_*` | No | Payment gateway credentials |
| `ZO_API_KEY` | No | Mentor chat API |

## Deploy to Vercel

1. Push this repo to GitHub.
2. Import the project in [Vercel](https://vercel.com/new).
3. **Required** — add these in Vercel → Settings → Environment Variables:
   - `DATABASE_URL` — Neon pooled PostgreSQL URL (`postgresql://...?sslmode=require`)
   - `SESSION_SECRET` — long random string
   - `GEMINI_API_KEY` — for AI features
4. Redeploy after adding env vars (Deployments → Redeploy).
5. Vercel auto-detects Flask from `app.py`; static files are served from `public/`.

If you see `FUNCTION_INVOCATION_FAILED`, open Vercel → Logs. The most common cause is a missing or invalid `DATABASE_URL`.

## Neon database

Tables are created automatically on startup via SQLAlchemy `db.create_all()`. You can also apply `schema.sql` manually if needed.
