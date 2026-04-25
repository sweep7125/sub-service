# VPN/Proxy Config Service

Flask service that distributes per-user VPN/proxy configs in Mihomo/Clash, V2Ray, and legacy JSON formats.

## Quick start

1. Install deps:
   - `python -m pip install -r requirements.txt`
2. Configure files:
   - `users` and `servers`
   - templates in `templates/`
3. Set env vars:
   - `SECRET_PATH` (required)
   - `SOCK` (required for production)
4. Run:
   - Dev: `python main.py`
   - Prod: `python app.py`

## Config files

### users
Format:

```
uuid | short_id | link_path | comment | groups | mihomo_advanced
```

- `groups` is a comma-separated list. If empty, defaults to `default`.
- `mihomo_advanced` is optional (custom template filename in `templates/`).

Example:

```
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | xxxxxxxxxxxxxxxx | user1 | User One | default |
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | xxxxxxxxxxxxxxxx | vip1  | VIP User | vip     | vip-template.yaml
```

### servers
Format:

```
host | sni | dns | public_key | description | groups | type | uuid | short_id
```

- `type` is `internal` or `external`.
- `uuid` and `short_id` are used for external servers.

### templates
- `templates/xray.json`
- `templates/mihomo.yaml`
- `templates/v2ray.lst`
- optional keyword variants in same folder:
  - `mihomo_android.yaml`
  - `xray_cmfa_android.json`
  - `v2ray_clashmeta.lst`

Keyword rules:
- suffix after first `_` is keyword list
- match is case-insensitive substring against request `User-Agent`
- multiple `_` mean OR match (`mihomo_cmfa_android.yaml` -> `cmfa` or `android`)
- if no keyword variant matches, service uses base file
- `mihomo_advanced`, if set, still uses exact filename from `templates/`

## Endpoint

```
GET /{secret}/{user_path}/{format}
```

Formats: `json`, `v2ray`, `mihomo` (also `clash`, `mh`, `type3`).

## Deploy

Debian 13 installer/updater:

```bash
sudo ./scripts/install-debian.sh         # auto: install or update
sudo ./scripts/install-debian.sh install # fresh install
sudo ./scripts/install-debian.sh update  # code-only update
```

Default target: `/opt/sub-stub`.

Usage notes:

- run from repo root as `root` or via `sudo`
- `auto` picks `install` when `/opt/sub-stub/app.py` is missing, else `update`
- installer checks missing system packages and installs them with `apt`
- on first install it creates `/opt/sub-stub/.env` from `.env.example`
- if `.env` has no `SECRET_PATH` or still has placeholder, installer prints warning

Install mode copies runtime files, `servers`, `users`, `.env.example`, `.env`, templates, and installs default systemd unit.

Update mode refreshes only runtime code:

- `app.py`
- `main.py`
- `requirements.txt`
- `scripts/`
- `src/`

Update mode does not touch:

- `servers`
- `users`
- `.env`
- `templates/`
- `happ.routing`
- installed systemd unit

## User-Agent Policy

Subscription response policy can be tuned via `.env` regex variables:

- `SUBSCRIPTION_UA_WHITELIST_PATTERN`
- `SUBSCRIPTION_UA_BLOCKLIST_PATTERN`

Behavior:

- `SUBSCRIPTION_UA_WHITELIST_PATTERN`:
   - empty -> allow all
   - non-empty -> allow only matching User-Agent values
- `SUBSCRIPTION_UA_BLOCKLIST_PATTERN`:
   - empty -> block nothing
   - non-empty -> block matching User-Agent values

Both rules are applied together (allow by whitelist first, then deny by blocklist).
If a regex in `.env` is invalid, the service logs a warning and ignores that rule.

## Custom headers

Optional env vars:

```
CUSTOM_HEADER_1=name|value
CUSTOM_HEADER_2=name|value|user_agent_regex
```
