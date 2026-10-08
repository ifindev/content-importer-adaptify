#!/usr/bin/env bash
# One-time VPS and GitHub setup for the app, run from your own machine.
# Do the Firebase steps and the DNS records first (docs/deploy-vps.md).
#
#   make vps-setup
#
# It asks for each value. To skip the questions, set them first, for example
# APP_DOMAIN=app.example.com API_DOMAIN=... VPS=... AGENCY_EMAILS=...
# FIREBASE_API_KEY=... FIREBASE_KEY=... make vps-setup
#
# Safe to re-run: an existing ~/app/.env (and its encryption key) and nginx
# sites are kept.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."  # repo root

# Asks for any value not already set in the environment.
ask() {
  local var=$1
  if [ -z "${!var:-}" ]; then
    # No -r: a file dragged into Terminal arrives as a backslash-escaped path.
    # shellcheck disable=SC2162
    read -p "$2: " "${var?}"
  fi
  [ -n "${!var:-}" ] || { echo "$var is required" >&2; exit 1; }
}
ask APP_DOMAIN "Web app address, for example app.example.com"
ask API_DOMAIN "API address, for example api.example.com"
ask VPS "VPS login, for example ubuntu@203.0.113.10"
if [ -z "${VPS_PORT:-}" ]; then
  # shellcheck disable=SC2162
  read -p "VPS SSH port (press Enter for 22): " VPS_PORT
fi
VPS_PORT="${VPS_PORT:-22}"
ask AGENCY_EMAILS "Login emails, comma-separated with no spaces"
ask FIREBASE_API_KEY "Firebase web apiKey (starts with AIza)"
ask FIREBASE_KEY "Path to the Firebase key .json file (you can drag the file here)"
FIREBASE_KEY="${FIREBASE_KEY/#\~/$HOME}"  # a typed ~ isn't expanded by read
FIREBASE_KEY="${FIREBASE_KEY%"${FIREBASE_KEY##*[![:space:]]}"}"  # drag-and-drop adds a trailing space
[ -f "$FIREBASE_KEY" ] || { echo "No file at $FIREBASE_KEY" >&2; exit 1; }
DEPLOY_KEY="$HOME/.ssh/content-importer-deploy"
# Every ssh and scp below goes to the VPS, on its SSH port.
ssh() { command ssh -p "$VPS_PORT" "$@"; }
scp() { command scp -P "$VPS_PORT" "$@"; }
PROJECT_ID=$(python3 -c 'import json, sys; print(json.load(open(sys.argv[1]))["project_id"])' "$FIREBASE_KEY")

echo "==> Checking DNS and gh"
for host in "$APP_DOMAIN" "$API_DOMAIN"; do
  [ -n "$(dig +short "$host")" ] || { echo "$host doesn't resolve yet; add its A record first" >&2; exit 1; }
done
gh auth status >/dev/null

echo "==> Deploy key ($DEPLOY_KEY)"
[ -f "$DEPLOY_KEY" ] || ssh-keygen -q -t ed25519 -f "$DEPLOY_KEY" -N "" -C github-deploy
PUB=$(cat "$DEPLOY_KEY.pub")

echo "==> VPS: ~/app, .env, Firebase key, deploy key"
ssh "$VPS" "mkdir -p -m 700 ~/app"
scp -q "$FIREBASE_KEY" "$VPS:app/firebase-service-account.json"
sed "s/app\.example\.com/$APP_DOMAIN/" infra/app/nginx/app.conf | ssh "$VPS" "cat > ~/app/nginx-app.conf"
sed "s/api\.example\.com/$API_DOMAIN/" infra/app/nginx/api.conf | ssh "$VPS" "cat > ~/app/nginx-api.conf"
ssh "$VPS" "APP_DOMAIN=$APP_DOMAIN AGENCY_EMAILS=$(printf %q "$AGENCY_EMAILS") PUB=$(printf %q "$PUB") bash -s" <<'REMOTE'
set -euo pipefail
cd ~/app
# 644 so the container's non-root user can read it; ~/app itself is 700.
chmod 644 firebase-service-account.json
if [ -f .env ]; then
  echo "    ~/app/.env exists, keeping it"
else
  umask 077
  # A Fernet key is 32 random bytes in URL-safe base64.
  cat > .env <<ENV
WEB_BASE_URL=https://$APP_DOMAIN
CREDENTIAL_ENCRYPTION_KEY=$(openssl rand -base64 32 | tr '+/' '-_')
INTERNAL_API_SECRET=$(openssl rand -base64 32)
AGENCY_EMAILS=$AGENCY_EMAILS
ENV
  echo "    wrote ~/app/.env; copy CREDENTIAL_ENCRYPTION_KEY from it to your password manager"
fi
mkdir -p -m 700 ~/.ssh
grep -qxF "$PUB" ~/.ssh/authorized_keys 2>/dev/null || echo "$PUB" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
REMOTE

echo "==> VPS: docker group, nginx sites, certificate (sudo may ask for your password)"
# Each site is installed only once: certbot edits it to add HTTPS.
ssh -t "$VPS" "sudo usermod -aG docker \"\$USER\" \
  && for site in app:$APP_DOMAIN api:$API_DOMAIN; do \
       f=/etc/nginx/sites-available/\${site#*:}; \
       [ -f \$f ] || sudo install -m 644 ~/app/nginx-\${site%%:*}.conf \$f; \
       sudo ln -sf \$f /etc/nginx/sites-enabled/; rm ~/app/nginx-\${site%%:*}.conf; \
     done \
  && sudo nginx -t && sudo systemctl reload nginx \
  && sudo certbot --nginx -d $APP_DOMAIN -d $API_DOMAIN --non-interactive --agree-tos --redirect"

echo "==> Checking the deploy key can run docker"
ssh -i "$DEPLOY_KEY" -o IdentitiesOnly=yes "$VPS" docker ps >/dev/null

echo "==> GitHub variables and secrets"
gh variable set VPS_SSH --body "$VPS"
gh variable set VPS_PORT --body "$VPS_PORT"
gh variable set FIREBASE_API_KEY --body "$FIREBASE_API_KEY"
gh variable set FIREBASE_AUTH_DOMAIN --body "$PROJECT_ID.firebaseapp.com"
gh variable set FIREBASE_PROJECT_ID --body "$PROJECT_ID"
gh secret set VPS_SSH_KEY < "$DEPLOY_KEY"
ssh-keyscan -p "$VPS_PORT" "${VPS#*@}" 2>/dev/null | gh secret set VPS_KNOWN_HOSTS

echo "==> Done. Delete $FIREBASE_KEY from this Mac, then deploy by pushing to main or:"
echo "    gh run rerun \$(gh run list --workflow ci.yml --branch main --limit 1 --json databaseId -q '.[0].databaseId') --failed"
