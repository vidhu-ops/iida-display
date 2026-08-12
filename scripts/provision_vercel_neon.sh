#!/usr/bin/env bash
#
# ⚠️  RUN THIS IN YOUR TERMINAL — NOT IN THE NEON SQL EDITOR
#     Neon SQL only accepts SQL (see schema.sql). Bash scripts cause:
#     ERROR: syntax error at or near "#!/" (SQLSTATE 42601)
#
# Provision a fresh Neon database for this Vercel project and redeploy.
#
# Fixes: "The endpoint has been disabled" when DATABASE_URL points at a dead
# Neon compute endpoint.
#
# Usage:
#   npx vercel login
#   npx vercel link
#   ./scripts/provision_vercel_neon.sh
#
# Requires: Vercel CLI logged in with access to the iida-display project.

set -euo pipefail

VERCEL_CMD=(vercel)
if ! command -v vercel >/dev/null 2>&1; then
  VERCEL_CMD=(npx vercel)
fi

echo "==> Removing stale DATABASE_URL (if any) ..."
for env in production preview development; do
  "${VERCEL_CMD[@]}" env rm DATABASE_URL "$env" -y >/dev/null 2>&1 || true
done

echo "==> Installing Neon via Vercel Marketplace ..."
"${VERCEL_CMD[@]}" integration add neon \
  --name iida-display-db \
  --environment production \
  --environment preview \
  --environment development \
  --non-interactive

echo "==> Pulling env vars locally (.env.local) ..."
"${VERCEL_CMD[@]}" env pull .env.local --yes >/dev/null 2>&1 || "${VERCEL_CMD[@]}" env pull .env.local

if ! grep -q '^DATABASE_URL=' .env.local; then
  echo "ERROR: Neon install did not create DATABASE_URL. Check Vercel → Storage."
  exit 1
fi

echo "==> Ensure SESSION_SECRET and GROQ_API_KEY are set on Vercel."
echo "    (Add them in Settings → Environment Variables if missing.)"

echo "==> Deploying to production ..."
"${VERCEL_CMD[@]}" --prod

echo
echo "Done. Verify:"
echo "  curl -s https://iida-display.vercel.app/status | python3 -m json.tool"
