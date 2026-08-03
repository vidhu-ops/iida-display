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

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes (prod) | Neon PostgreSQL connection string (`?sslmode=require`) |
| `SESSION_SECRET` | Yes | Flask session signing key |
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `ZO_API_KEY` | No | Mentor chat API |
| `CASHFREE_*` | No | Payment gateway credentials |

For Vercel, use `vercel.env.example` as the checklist.

## Deploy to Vercel

Project: **sheeyameela-4868s-projects/iida-display**  
Production URL: https://iida-display.vercel.app

### 1. Set environment variables

In **Vercel → Settings → Environment Variables**, add (Production + Preview):

1. `DATABASE_URL` — Neon **pooled** URL ending with `?sslmode=require`
2. `SESSION_SECRET` — e.g. `openssl rand -hex 32`
3. `GEMINI_API_KEY` — from Google AI Studio

Or fill `vercel.env.example` → `.env.vercel` and run:

```bash
cp vercel.env.example .env.vercel
# edit .env.vercel with real values
npx vercel login
npx vercel link
./scripts/push_vercel_env.sh
```

Neon Marketplace integration vars (`*_DATABASE_URL`, `*_POSTGRES_URL`) are also accepted if `DATABASE_URL` is unset.

### 2. Redeploy

After changing env vars you **must** redeploy:

```bash
npx vercel --prod
```

Or: Vercel → Deployments → ⋯ → Redeploy.

### 3. Verify

```bash
curl -s https://iida-display.vercel.app/health
curl -s https://iida-display.vercel.app/status
```

`/status` should show `database_ping: true` and `status: "ok"`.

### Neon endpoint disabled?

If `/status` reports `The endpoint has been disabled`:

1. Open [Neon Console](https://console.neon.tech) and enable the compute, **or** create a new project
2. Copy the pooled connection string
3. Update `DATABASE_URL` on Vercel
4. Redeploy

## Neon database

Tables are created automatically on startup via SQLAlchemy `db.create_all()`. You can also apply `schema.sql` manually if needed.
