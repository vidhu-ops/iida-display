# IIDA Display

Flask web app for business intelligence, planning, mentor chat, and payments. Configured for **Vercel** + **Neon PostgreSQL**.

## Deploy to Vercel

> **Deploy failing with "Provisioning integrations failed"?**  
> See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) — usually Neon branch limit (10 max) or a disabled endpoint.

### Option A — One command (recommended)

From this repo on your machine (**terminal**, not Neon SQL editor):

```bash
npx vercel login
npx vercel link
./scripts/provision_vercel_neon.sh
```

This removes a stale `DATABASE_URL`, provisions Neon via the Vercel Marketplace, and deploys to production.

> **Note:** Do not paste `provision_vercel_neon.sh` into the Neon SQL Editor — use `schema.sql` if you need manual SQL, or let the app create tables on deploy.

### Option B — Vercel dashboard

1. [Import this repo](https://vercel.com/new) into Vercel
2. **Storage → Add → Neon** (creates `DATABASE_URL` automatically)
3. Add **Environment Variables** (Production):
   - `SESSION_SECRET` — run `openssl rand -hex 32`
   - `GROQ_API_KEY` — from [Groq Console](https://console.groq.com/keys)
4. **Deployments → Redeploy**

### Fix: "endpoint has been disabled"

Your `DATABASE_URL` points at a **disabled Neon compute endpoint**. Either:

- Run `./scripts/provision_vercel_neon.sh` (creates a fresh Neon DB), **or**
- Neon Console → enable the endpoint → copy pooled URL → update `DATABASE_URL` on Vercel → redeploy

Verify: `curl -s https://iida-display.vercel.app/status` should show `"database_ping": true`.

## Required environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` or `database_POSTGRES_URL` | Yes | Neon pooled URL — auto-set by Neon integration |
| `SESSION_SECRET` | Yes | Flask session key |
| `GROQ_API_KEY` | Yes | Groq API key for AI reports |

See `vercel.env.example` for optional vars (ZO mentor chat, Cashfree payments).

## Local development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
python main.py
```

## GitHub Actions (optional)

Add repository secrets `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID` to auto-deploy on push to `main`.

## Stack

- Python 3.11 + Flask
- SQLAlchemy + PostgreSQL (Neon)
- Groq (Llama) for AI reports
