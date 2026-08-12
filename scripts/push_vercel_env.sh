#!/usr/bin/env bash
# Push required (and any filled optional) env vars from a local env file to Vercel.
#
# Usage:
#   1. cp vercel.env.example .env.vercel
#   2. Fill in real values in .env.vercel (never commit this file)
#   3. npx vercel login && npx vercel link
#   4. ./scripts/push_vercel_env.sh
#   5. Redeploy: npx vercel --prod  (or Redeploy in the dashboard)
#
# Requires: vercel CLI authenticated against sheeyameela-4868s-projects/iida-display

set -euo pipefail

ENV_FILE="${1:-.env.vercel}"
TARGETS="${VERCEL_ENV_TARGETS:-production preview development}"

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Missing $ENV_FILE"
  echo "Run: cp vercel.env.example .env.vercel  && edit values"
  exit 1
fi

if ! command -v vercel >/dev/null 2>&1 && ! command -v npx >/dev/null 2>&1; then
  echo "Install Vercel CLI: npm i -g vercel"
  exit 1
fi

VERCEL_CMD=(vercel)
if ! command -v vercel >/dev/null 2>&1; then
  VERCEL_CMD=(npx vercel)
fi

REQUIRED=(DATABASE_URL SESSION_SECRET GROQ_API_KEY)
OPTIONAL=(
  ZO_API_KEY ZO_BASE_URL ZO_MODEL ANTHROPIC_API_KEY
  CASHFREE_APP_ID CASHFREE_API_KEY CASHFREE_API_URL
  CASHFREE_FORM_ID CASHFREE_SUBSCRIPTION_FORM_URL CASHFREE_SUBSCRIPTION_FORM_ID
)

get_value() {
  local key="$1"
  # shellcheck disable=SC2002
  local line
  line="$(grep -E "^${key}=" "$ENV_FILE" | tail -n1 || true)"
  [[ -z "$line" ]] && return 1
  printf '%s' "${line#*=}"
}

is_placeholder() {
  local value="$1"
  case "$value" in
    ''|your-*|replace-*|postgresql://USER:*|postgresql://user:*)
      return 0
      ;;
  esac
  return 1
}

push_var() {
  local key="$1"
  local value="$2"
  local target
  for target in $TARGETS; do
    echo "→ Setting $key for $target"
    # Remove existing value if present (ignore errors), then add.
    printf '%s\n' "$value" | "${VERCEL_CMD[@]}" env rm "$key" "$target" -y >/dev/null 2>&1 || true
    printf '%s\n' "$value" | "${VERCEL_CMD[@]}" env add "$key" "$target" >/dev/null
  done
}

echo "Reading $ENV_FILE ..."
missing=0
for key in "${REQUIRED[@]}"; do
  if ! value="$(get_value "$key")"; then
    echo "ERROR: required $key missing from $ENV_FILE"
    missing=1
    continue
  fi
  if is_placeholder "$value"; then
    echo "ERROR: required $key still has a placeholder value"
    missing=1
    continue
  fi
  push_var "$key" "$value"
done

for key in "${OPTIONAL[@]}"; do
  if value="$(get_value "$key")"; then
    if ! is_placeholder "$value"; then
      push_var "$key" "$value"
    fi
  fi
done

if [[ "$missing" -ne 0 ]]; then
  echo
  echo "Fix the required placeholders in $ENV_FILE and re-run."
  exit 1
fi

echo
echo "Done. Redeploy so the new env vars take effect:"
echo "  npx vercel --prod"
echo "Then verify: curl -s https://iida-display.vercel.app/status"
