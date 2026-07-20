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

This project is linked to **sheeyameela-4868s-projects/iida-display** on Vercel.

Environment variables already configured on Vercel:
- `DATABASE_URL` (Neon PostgreSQL)
- `SESSION_SECRET`

Optional — add in Vercel → Settings → Environment Variables:
- `GEMINI_API_KEY` — required for AI report generation
- `CASHFREE_*` — required for payments
- `ZO_API_KEY` — required for mentor chat

After pushing to GitHub, redeploy from the Vercel dashboard or run:

```bash
npx vercel --prod
```

Verify deployment: `https://your-app.vercel.app/health` should return `{"status":"ok"}`.

## Neon database

Tables are created automatically on startup via SQLAlchemy `db.create_all()`. You can also apply `schema.sql` manually if needed.
