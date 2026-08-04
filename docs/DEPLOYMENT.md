# Vercel + Neon deployment troubleshooting

## Error: `Provisioning integrations failed`

**Symptom:** Build never starts. Vercel logs show:

```
Provisioning Integrations
iida / neon-almond-island
Create database branch for deployment  → FAILED
```

### Root cause

The **Neon ↔ Vercel integration** tries to create a new database branch for every deployment. This fails when:

1. **Neon free plan branch limit hit** (max **10 branches** including `main` and all `preview/*` branches) — most common
2. **Parent Neon compute endpoint is disabled** (your old `ep-shy-wave-...` endpoint)
3. **Deploying from a feature branch** (`v0/neon-database-connection-...`) triggers extra preview branches

Your production site still points at the **disabled** endpoint, so even a successful deploy would fail at runtime until `DATABASE_URL` is fixed.

---

## Fix (do these in order)

### Step 1 — Free up Neon branches

1. Open [console.neon.tech](https://console.neon.tech)
2. Open project **neon-almond-island** (or the project linked to integration `iida`)
3. Go to **Branches**
4. Delete old branches, especially:
   - `preview/v0-neon-database-connection-*`
   - `preview/cursor-*`
   - Any unused `preview/*` branches
5. Keep **main** (or your primary branch) — aim for **under 10 total branches**

### Step 2 — Enable auto-cleanup (prevents repeat failures)

**Neon Console → Integrations → Vercel → Manage:**

- Enable **Automatically delete obsolete Neon branches**

**Or in Vercel:** Project → **Storage** → your Neon resource → Settings → enable branch cleanup if available.

### Step 3 — Fix production branch in Vercel

Your deploy is coming from `v0/neon-database-connection-71d97174`. For production, use `main`:

1. Vercel → **iida-display** → **Settings → Git**
2. Set **Production Branch** to `main`
3. Merge https://github.com/vidhu-ops/iida-display/pull/1 into `main` first (has DB fallback + deploy scripts)

### Step 4 — Fix `DATABASE_URL`

Either:

**A) Refresh Neon integration (recommended)**

1. Vercel → **Storage** → Neon (`iida` / `neon-almond-island`)
2. If the database looks broken, **disconnect** the old integration
3. **Add → Neon** again (creates fresh `DATABASE_URL`)
4. Delete any manual `DATABASE_URL` pointing at `ep-shy-wave-aexq3vgh`

**B) Manual**

1. Neon Console → enable compute OR create new project
2. Copy **pooled** connection string (`?sslmode=require`)
3. Vercel → **Settings → Environment Variables** → update `DATABASE_URL` for Production

### Step 5 — Redeploy

Vercel → **Deployments** → **Redeploy** (or push to `main`).

Verify:

```bash
curl -s https://iida-display.vercel.app/status
```

Expect: `"database_ping": true`, `"status": "ok"`.

---

## Ask Vercel Agent (copy-paste)

```
My iida-display production deployment fails with "Provisioning integrations failed"
during Neon step "Create database branch for deployment" (integration: iida / neon-almond-island).

Please:
1. Check if Neon branch limit is exceeded and tell me which preview/* branches to delete
2. Enable automatic deletion of obsolete Neon branches
3. Set production branch to main (not v0/neon-database-connection-71d97174)
4. Replace broken DATABASE_URL (ep-shy-wave-aexq3vgh disabled endpoint) with a working Neon connection
5. Confirm SESSION_SECRET and GEMINI_API_KEY are set for Production
6. Redeploy production and verify /status shows database_ping: true
```

---

## If you want to skip preview DB branches entirely

Disconnect the Neon integration and set `DATABASE_URL` manually (see `vercel.env.example`). Preview deployments will share the same database — fine for solo development, not ideal for teams.

```bash
npx vercel login
npx vercel link
./scripts/provision_vercel_neon.sh
```
