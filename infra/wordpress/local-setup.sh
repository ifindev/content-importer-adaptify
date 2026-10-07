#!/usr/bin/env bash
# Idempotent local WordPress setup: installs WordPress via wp-cli, sets
# pretty permalinks, and (re)creates an application password for the app,
# writing WP_BASE_URL / WP_USERNAME / WP_APP_PASSWORD into .env.
set -euo pipefail

cd "$(dirname "${BASH_SOURCE[0]}")/../.."  # repo root

ENV_FILE=".env"
WP_URL="http://localhost:8080"
WP_ADMIN_USER="admin"
WP_ADMIN_PASSWORD="admin"       # local-only throwaway login, not the app password
WP_ADMIN_EMAIL="admin@example.test"
APP_PASSWORD_NAME="content-importer"

wp() {
  docker compose run --rm -T wp-cli wp "$@"
}

echo "==> Waiting for WordPress/MariaDB to be reachable..."
for i in $(seq 1 30); do
  wp core version >/dev/null 2>&1 && break
  [ "$i" -eq 30 ] && { echo "WordPress did not become reachable in time" >&2; exit 1; }
  sleep 2
done

if wp core is-installed >/dev/null 2>&1; then
  echo "==> WordPress already installed, skipping core install"
else
  echo "==> Installing WordPress"
  wp core install \
    --url="$WP_URL" \
    --title="Content Importer Local" \
    --admin_user="$WP_ADMIN_USER" \
    --admin_password="$WP_ADMIN_PASSWORD" \
    --admin_email="$WP_ADMIN_EMAIL" \
    --skip-email
fi

echo "==> Setting pretty permalinks"
wp rewrite structure '/%postname%/' --hard

echo "==> Replacing application password '$APP_PASSWORD_NAME' if it exists"
EXISTING_UUID=$(wp user application-password list "$WP_ADMIN_USER" --format=csv --fields=uuid,name 2>/dev/null \
  | awk -F',' -v name="$APP_PASSWORD_NAME" '$2 == name {print $1}')
[ -n "${EXISTING_UUID:-}" ] && wp user application-password delete "$WP_ADMIN_USER" "$EXISTING_UUID"

APP_PASSWORD=$(wp user application-password create "$WP_ADMIN_USER" "$APP_PASSWORD_NAME" --porcelain)

echo "==> Writing WP_BASE_URL / WP_USERNAME / WP_APP_PASSWORD into $ENV_FILE"
upsert_env() {
  local key="$1" value="$2"
  if grep -q "^${key}=" "$ENV_FILE" 2>/dev/null; then
    sed -i.bak "s|^${key}=.*|${key}=${value}|" "$ENV_FILE" && rm -f "${ENV_FILE}.bak"
  else
    echo "${key}=${value}" >> "$ENV_FILE"
  fi
}
upsert_env "WP_BASE_URL" "$WP_URL"
upsert_env "WP_USERNAME" "$WP_ADMIN_USER"
upsert_env "WP_APP_PASSWORD" "$APP_PASSWORD"

echo "==> Done. WordPress is ready at $WP_URL/wp-admin (login: $WP_ADMIN_USER / $WP_ADMIN_PASSWORD)"
