#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"
set -a; . ./.env; set +a

DEST="/var/backups/wordpress/$(date +%F)"
mkdir -p "$DEST"

docker compose exec -T -e MYSQL_PWD="$DB_ROOT_PASSWORD" db \
  mariadb-dump -u root wordpress | gzip > "$DEST/db.sql.gz"

docker compose exec -T wordpress \
  tar czf - -C /var/www/html . > "$DEST/wp_files.tar.gz"

find /var/backups/wordpress -mindepth 1 -maxdepth 1 -type d -mtime +7 -exec rm -rf {} +
