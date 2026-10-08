# T-043 WordPress on the VPS

**Phase:** 5 · Infra · **Status:** done · **Size:** S
**Refs:** spec: WordPress integration, Risks; architecture: WordPress on the VPS, VPS setup once
**Depends on:** —

## Goal
`https://wp.aiwitharifin.com` runs a WordPress the deployed API can publish to, and scheduled posts go live on time even when nobody visits the site.

## Analysis

### The VPS
Tencent Cloud, 2 vCPU, about 4 GB RAM, 59 GB disk, Ubuntu 24.04 LTS, IP `43.133.156.209`. You are the only user. WordPress and MariaDB need well under 1 GB.

Already installed: Docker (through `get.docker.com`, which adds Docker's apt repository and the compose plugin) and nginx.

**Precondition:** check the instance's region. In mainland China regions, a domain served on ports 80/443 needs an ICP filing, and the traffic is blocked without one. Regions outside mainland China (Hong Kong, Singapore, Jakarta, …) don't.

### Layout
| Where | What |
| --- | --- |
| Host (Ubuntu) | nginx as the reverse proxy, certbot for HTTPS, cron, `ufw` |
| Docker Compose | `wordpress` and `db` only |

- **Don't install** `mariadb-server`, `php-fpm` or any `php-*` package on the host. The containers hold them.
- **nginx on the host:** it's already installed, and certbot manages its certificates directly (`python3-certbot-nginx` installs a renewal timer).
- **Manual setup:** the server is set up once and rarely changes. The files below live in the repo, so a rebuild is about 30 minutes of following the README.

### Files in `infra/wordpress/`
Next to the existing `local-setup.sh`, which stays for local use.

**`docker-compose.yml`** (production; the local WordPress stays in the root compose file)
```yaml
services:
  db:
    image: mariadb:11
    restart: unless-stopped
    environment:
      MARIADB_DATABASE: wordpress
      MARIADB_USER: wpuser
      MARIADB_PASSWORD: ${DB_PASSWORD}
      MARIADB_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - db_data:/var/lib/mysql

  wordpress:
    image: wordpress:php8.3-apache
    restart: unless-stopped
    depends_on:
      - db
    ports:
      - "127.0.0.1:8080:80"
    environment:
      WORDPRESS_DB_HOST: db
      WORDPRESS_DB_NAME: wordpress
      WORDPRESS_DB_USER: wpuser
      WORDPRESS_DB_PASSWORD: ${DB_PASSWORD}
      WORDPRESS_CONFIG_EXTRA: |
        define('DISABLE_WP_CRON', true);
        if (($$_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https') { $$_SERVER['HTTPS'] = 'on'; }
    volumes:
      - wp_data:/var/www/html

volumes:
  db_data:
  wp_data:
```
- `127.0.0.1:8080:80` makes WordPress reachable from the VPS only. Docker writes its own iptables rules, which run before `ufw`, so a plain `"8080:80"` would be open to the internet whatever `ufw` says.
- `db` has no `ports:`, so MariaDB stays on the internal Docker network.
- `WORDPRESS_CONFIG_EXTRA` is read by the official image's `wp-config.php`. It survives rebuilds, unlike a `sed` edit of the file. `$$` is compose's escape for a literal `$`.
  - `DISABLE_WP_CRON`: WordPress's own scheduler only runs on page visits. The host cron below replaces it.
  - The HTTPS line: nginx ends TLS and talks plain HTTP to the container. Without this line WordPress thinks it's on HTTP. It then turns application passwords off and builds `http://` links, which redirect in a loop.

**`nginx/wp.aiwitharifin.com.conf`** (copied to `/etc/nginx/sites-available/`)
```nginx
server {
    listen 80;
    server_name wp.aiwitharifin.com;
    client_max_body_size 64M;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```
Certbot adds the `listen 443 ssl` block and the HTTP-to-HTTPS redirect when it runs. Commit the file as written above; the certbot additions stay on the server.

**`.env.example`**: `DB_PASSWORD=`, `DB_ROOT_PASSWORD=`. The real `.env` lives only on the VPS.

**`backup.sh`** (in the repo, copied from the VPS)
- `set -euo pipefail`; reads `.env` from its own folder.
- Dumps the database with `docker compose exec -T -e MYSQL_PWD=… db mariadb-dump -u root wordpress | gzip` → `/var/backups/wordpress/<date>/db.sql.gz`. `MYSQL_PWD` keeps the password out of the process list.
- Tars `/var/www/html` from inside the `wordpress` container (`docker compose exec -T wordpress tar czf - …`) → `wp_files.tar.gz`. No extra container or volume name needed.
- Deletes backup folders older than 7 days.

**`crontab.txt`**: the two cron lines below, with the real path.

**`README.md`**: the setup steps below, short.

### Setup steps, once, by hand
1. **DNS:** an `A` record `wp` → `43.133.156.209`. Wait until `dig +short wp.aiwitharifin.com` returns it. The root `aiwitharifin.com` stays free.
2. **Firewall:** allow only 22, 80 and 443 in the Tencent security group (or Lighthouse firewall) **and** in `ufw` (`ufw allow OpenSSH`, `ufw allow 'Nginx Full'`, `ufw enable`). The cloud firewall sits in front of the VM, so Docker can't bypass it; it's the strongest layer.
3. **SSH and updates:** key login only (`PasswordAuthentication no`). Turn on `unattended-upgrades`.
4. **Packages:** `sudo apt install certbot python3-certbot-nginx -y` (Docker and nginx are already installed).
5. **WordPress containers:** copy `infra/wordpress/` to `/home/<user>/wordpress`, create `.env` from `.env.example` with long random passwords, `docker compose up -d`. Check with `docker compose ps` and `curl -I http://127.0.0.1:8080` (expect 302 or 200).
6. **nginx:** copy the site config to `/etc/nginx/sites-available/wp.aiwitharifin.com`, link it into `sites-enabled`, remove `sites-enabled/default`, then `sudo nginx -t && sudo systemctl reload nginx`.
7. **HTTPS:** `sudo certbot --nginx -d wp.aiwitharifin.com`, and choose the redirect option. Check renewal with `sudo certbot renew --dry-run`.
8. **Install WordPress** in the browser at `https://wp.aiwitharifin.com`: site title, an admin user with a strong password (kept in your password manager). Settings → Permalinks → "Post name". Install no security plugins (spec Risks: they can block the REST API).
9. **App user:** create user `content-importer` with the **Author** role. In its profile, create an application password named `content-importer-app`. It is shown once; keep it for T-045 and T-047.
10. **Cron** (`crontab -e` as your user):
    ```
    * * * * * curl -s -m 50 -o /dev/null http://127.0.0.1:8080/wp-cron.php
    0 3 * * * $HOME/wordpress/backup.sh >> $HOME/backup.log 2>&1
    ```
    The scheduler line calls WordPress on the host's loopback port. An earlier version used `docker compose exec -T wordpress curl …`: it worked by hand but hung under cron (no terminal), so posts missed their time.
    Cron sets `$HOME`, so `$HOME` works; `~` may not. `/var/backups/wordpress` must be writable by your user (`sudo mkdir -p /var/backups/wordpress && sudo chown <user> /var/backups/wordpress`).

### Why an Author, not admin
The app only creates, reschedules and trashes posts it made itself (spec: WordPress integration, Calls). An Author can do all of that for their own posts. If the stored app password leaked, it couldn't install plugins, manage users, change settings, or touch other people's posts. Its posts show "content-importer" as the author, which is fine for a demo site.

### The `docker` group
Your user is in the `docker` group, which is effectively root. That's acceptable because you're the only user. If someone else ever gets an account, remove yourself from the group and use `sudo docker …`.

### Edge cases
| Case | Behavior |
| --- | --- |
| VPS reboots | nginx starts as a service; the containers restart (`unless-stopped`); cron runs again. Posts due while it was down publish on the next cron run, and the app shows Late until then (spec Risks). |
| Certificate renewal | certbot's systemd timer renews it and reloads nginx. |
| WordPress core update | Minor versions update themselves. For a new image, `docker compose pull && docker compose up -d`; data is on the volumes. |
| Disk fills with backups | 7-day retention; a backup at demo scale is a few MB. |
| Port 8080 already used on the host | Check with `sudo ss -tlnp \| grep 8080` before step 5, and pick another local port in both the compose file and the nginx config. |

### Decisions
- nginx and certbot on the host as the reverse proxy, with only WordPress and MariaDB in Docker. This replaces Caddy from the earlier plan, since nginx was already installed.
- Update architecture "WordPress on the VPS": nginx and certbot on the host, `127.0.0.1` port binding, `WORDPRESS_CONFIG_EXTRA` (scheduler off, HTTPS detection), the Author user for the app password, nightly backups kept 7 days. Architecture currently says "WordPress, MariaDB, and Caddy" containers.
- Update architecture "VPS setup, once" to match the steps above. It currently says "create an application password under the admin user's profile".

## Acceptance criteria
- [x] `https://wp.aiwitharifin.com` loads with a valid certificate, and `http://` redirects to `https://`.
- [x] `sudo certbot renew --dry-run` succeeds.
- [x] `sudo ss -tlnp` shows 8080 on `127.0.0.1` only, and nothing on 3306.
- [ ] From outside, only the SSH port (2222 on this VPS), 80 and 443 answer. Not checked with a port scan yet.
- [x] `curl -u content-importer:'<app password>' "https://wp.aiwitharifin.com/wp-json/wp/v2/users/me?context=edit"` returns 200.
- [x] As the Author, through REST: create a post with `status: future` 3 minutes ahead; it goes `publish` on time with no visits to the site.
- [ ] As the Author, `DELETE /wp/v2/posts/{id}` moves it to the trash. Not checked yet; T-045's live run covers it (Unschedule).
- [x] As the Author, `GET /wp-json/wp/v2/plugins` returns 403.
- [x] `backup.sh` writes `db.sql.gz` and `wp_files.tar.gz`.
- [ ] The dump restores into a scratch MariaDB container. Not checked yet.
- [x] architecture.md updated as listed in Decisions.

## Tasks
- [x] Check the VPS region (ICP precondition).
- [x] Write `docker-compose.yml`, `nginx/wp.aiwitharifin.com.conf`, `.env.example`, `backup.sh` and `crontab.txt` in `infra/wordpress/`. No separate README: the steps live in architecture "VPS setup, once".
- [x] DNS record and firewall.
- [ ] Confirm SSH key-only login and `unattended-upgrades`.
- [x] Install certbot; start the containers; set up the nginx site; get the certificate.
- [x] Finish the WordPress install; set permalinks.
- [x] Create the Author user and its application password.
- [x] Add both cron lines; run `backup.sh` once by hand.
- [x] Run the checks above.
- [x] Update architecture.md.

## Out of scope
- Off-site backups (copying backups off the VPS).
- Monitoring and uptime alerts for the VPS.
- Automated provisioning (Ansible, a setup script, Terraform for Tencent). Revisit if the server needs rebuilding more than once.
- Dokploy or any other PaaS layer, and Caddy.
