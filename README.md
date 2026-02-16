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
- `templates/v2ray-template.json`
- `templates/mihomo-template.yaml`
- `templates/v2ray-url-template.txt`

## Endpoint

```
GET /{secret}/{user_path}/{format}
```

Formats: `json`, `v2ray`, `mihomo` (also `clash`, `mh`, `type3`).

## Custom headers

Optional env vars:

```
CUSTOM_HEADER_1=name|value
CUSTOM_HEADER_2=name|value|user_agent_regex
```
