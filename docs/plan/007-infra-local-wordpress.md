# T-007 Local WordPress

**Phase:** 2 · Local infra · **Status:** analyzed · **Size:** M
**Refs:** spec: WordPress integration › Authentication; architecture: Infrastructure › Local setup
**Depends on:** T-006

## Goal
A local WordPress that behaves like the VPS one for everything the app uses, and that anyone can set up with one command, including the application password.

## Analysis

### Flow
1. `make up` starts `wordpress` and `mariadb` with the other services.
2. `make wp-setup` (first run only) uses wp-cli to install WordPress, set pretty permalinks, and create an application password for the admin user. It writes `WP_BASE_URL`, `WP_USERNAME`, and `WP_APP_PASSWORD` into `.env`.
3. `make wp-cron` calls `wp-cron.php` once, which publishes any scheduled post whose time has passed.

### Config
| Setting | Value | Why |
| --- | --- | --- |
| Images | `wordpress:6-apache`, `mariadb:11`, `wordpress:cli` (setup only) | Matches the VPS stack |
| `WP_ENVIRONMENT_TYPE` | `local` (via `WORDPRESS_CONFIG_EXTRA`) | Application passwords need HTTPS unless the site is local |
| `DISABLE_WP_CRON` | `true` | Same as the VPS: scheduling runs only when cron is called |
| Permalinks | `/%postname%/` | `/wp-json/` routes need pretty permalinks; plain permalinks only serve `?rest_route=` |
| Host port | `8080` | `http://localhost:8080/wp-admin` for manual checks |

### Edge cases
| Case | Behavior |
| --- | --- |
| `make wp-setup` run twice | Skips install if WordPress is already installed; replaces the old `content-importer` application password instead of adding another |
| Volumes deleted | `make wp-setup` again rebuilds everything |
| API calls `http://wordpress` while the site URL is `http://localhost:8080` | Must not redirect REST calls. Verify in this ticket. If it does, set `WP_HOME`/`WP_SITEURL` per request host or call through `host.docker.internal:8080` |

### Open questions
- Does WordPress redirect REST requests whose Host differs from `siteurl`? **Default:** assume no; verify (see edge cases).

## Acceptance criteria
- [ ] `make up && make wp-setup` on a fresh clone gives a working site with an application password in `.env`
- [ ] From the api container, `GET http://wordpress/wp-json/wp/v2/users/me?context=edit` with Basic auth returns the admin user
- [ ] Without auth, the same call returns 401
- [ ] `make wp-cron` returns 200
- [ ] `make wp-reset` wipes the WordPress and database volumes
- [ ] `.env.example` lists `WP_BASE_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`, and the database variables

## Tasks
- [ ] Add `wordpress`, `mariadb` to `docker-compose.yml` with named volumes and a healthcheck on MariaDB
- [ ] `infra/wordpress/local-setup.sh` (wp-cli: install, rewrite structure, application password, write to `.env`)
- [ ] Makefile targets: `wp-setup`, `wp-cron`, `wp-reset`
- [ ] Update `.env.example`

## Out of scope
- VPS setup with Caddy (Phase 5)
- The app's own WordPress adapter (T-009)
