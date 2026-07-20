# Replit redirect for iidatech.com

Replit hosts your domain. Republish this tiny app on the **same Replit project** linked to `iidatech.com` to redirect all traffic to Vercel.

## Steps (5 minutes)

1. Go to [replit.com](https://replit.com) and open the Repl that owns **iidatech.com**
2. Replace `main.py` with the file from this folder (or copy all files here into the Repl root)
3. Replace `requirements.txt` with the one here
4. Click **Deploy** → **Publish** (Autoscale deployment)
5. Wait ~1 minute, then visit https://iidatech.com — it should redirect to https://iida-display-nu.vercel.app

## Files

- `main.py` — 301 redirect to Vercel (preserves paths and query strings)
- `requirements.txt` — Flask + gunicorn only
- `.replit` — deployment config

## Long-term (optional)

To serve the app directly from Vercel on iidatech.com (no redirect), you'll need Name.com DNS access to point the domain to Vercel instead of Replit.
