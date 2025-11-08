# VPN/Proxy Configuration Management System

A Flask-based web service for distributing VPN/Proxy configurations to multiple clients in various formats (Mihomo/Clash, V2Ray, JSON configs).

## Features

- **Multiple Configuration Formats**: Mihomo/Clash Meta, V2Ray subscription links, and JSON configs
- **Group-Based Access Control**: Flexible user and server grouping system for access management
- **User Management**: Multi-user support with individual credentials and personalized subscription links
- **Unified Server Management**: Single configuration file for all server types (internal/external)
- **Smart Caching**: File-based caching to minimize disk I/O
- **Geo Files Integration**: Automatic geo files update checking for Happ clients
- **Spider-X Generation**: Random path generation for Reality protocol obfuscation
- **Security Access Control**: Strict access control - only from localhost or HTTPS reverse proxy

## Project Structure

```
web-panel/
├── src/
│   ├── models/          # Data models (Server, User, Config)
│   ├── repositories/    # Data access layer with caching
│   ├── services/        # Business logic
│   ├── builders/        # Configuration builders
│   ├── utils/           # Utility functions
│   ├── web/             # Flask routes and HTTP handlers
│   └── constants.py     # Application constants
├── scripts/
│   └── prestart-pip-upgrade.sh  # Pre-start hook for systemd service
├── templates/           # Configuration templates
│   ├── v2ray-template.json
│   ├── mihomo-template.yaml
│   └── v2ray-url-template.txt
├── app.py               # WSGI entry point (production)
├── main.py              # Development entry point
├── servers              # Unified servers configuration
├── users                # Users credentials
├── happ.routing         # Happ client routing configuration
└── sub-stub.service     # Systemd service configuration
```

## 📋 Configuration Files

### users
User database with group-based access control and optional custom Mihomo templates:
```
uuid | short_id | link_path | comment | groups | mihomo_advanced
```
**Fields:**
- `uuid` - User's UUID for VPN connection
- `short_id` - Short ID for Reality protocol
- `link_path` - Custom path for user's subscription link
- `comment` - Human-readable name/description
- `groups` - Comma-separated group list
- `mihomo_advanced` - *(Optional)* Custom Mihomo template filename

**Examples:**
```
# Regular user with standard Mihomo template
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | xxxxxxxxxxxxxxxx | premium_user1 | Premium User | premium,vip |

# Advanced user with custom Mihomo template
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxy | xxxxxxxxxxxxxxyy | vip_user2 | VIP User | premium,vip | advanced-config.yaml
```

### servers
Unified server database (internal and external):
```
host | sni | dns | public_key | description | groups | type | uuid | short_id
```
**Example:**
```
premium-server-01.example.com | premium-server-01.example.com | https://dns.quad9.net/dns-query | PUBLIC_KEY | 🇸🇪 Premium Server 01 | premium,vip | internal
```

### templates/
Configuration templates directory:
- `v2ray-template.json` - V2Ray JSON configuration template
- `mihomo-template.yaml` - Default Mihomo YAML configuration template  
- `v2ray-url-template.txt` - VLESS URL template
- Custom templates - Create additional YAML files for per-user Mihomo configurations
- `README.md` - Template documentation

### happ.routing
JSON configuration for Happ client routing rules (DNS, geo files, domain/IP rules)

### scripts/
System integration scripts:
- `prestart-pip-upgrade.sh` - Pre-start hook for systemd service that upgrades pip dependencies

## 🚀 Quick Start

### Installation

1. Install dependencies:
```bash
pip install flask waitress pyyaml requests
```

2. Configure your files:
   - Edit `users` - add your users with groups
   - Edit `servers` - add your servers with groups
   - See files for format examples and documentation

3. Configure environment variables:
```bash
# Required for production
export SOCK=/path/to/socket
export SECRET_PATH=your_secret_path

# Optional
export SUBSTUB_CACHE_DIR=/var/cache/sub-stub
export LOG_LEVEL=INFO

# Custom HTTP Headers (see below for details)
export CUSTOM_HEADER_1=profile-update-interval|24
export CUSTOM_HEADER_2=profile-title|base64:VGVzdFRpdGxlRXhhbXBsZQ==
```

4. Run the application:

**Development:**
```bash
python main.py
```

**Production:**
```bash
python app.py
```

## Group-Based Access Control

The system uses groups to control which users can access which servers:

**How it works:**
- Users have groups: `premium,vip`
- Servers have groups: `premium,vip`
- Access granted if groups intersect
- Servers with no groups = accessible to all users

**Common groups:**
- `default` - Standard users and servers
- `premium` - High-speed premium servers
- `vip` - Maximum speed, all regions
- `family` - Family group
- `test` - Testing environment

## 🎨 Custom Mihomo Templates

You can create custom Mihomo configuration templates for individual users with personalized settings (ports, rules, DNS, etc.).

### How It Works

1. **Default behavior**: Users without `mihomo_advanced` field get standard `mihomo-template.yaml`
2. **Custom template**: Users with `mihomo_advanced` field get the specified template from `templates/` directory

### Setup Instructions

**Step 1: Create Custom Template**

Create a new YAML file in `templates/` directory (e.g., `templates/advanced-config.yaml`):

```yaml
# Custom ports for VIP users
mixed-port: 7891
allow-lan: true
mode: rule

# Proxy template (required)
proxy-template:
  type: vless
  network: tcp
  udp: true
  tls: true
  servername: placeholder
  uuid: placeholder
  flow: xtls-rprx-vision
  reality-opts:
    public-key: ""
    short-id: ""

# Custom proxy groups
proxy-groups:
  - name: "🚀 Auto Select"
    type: url-test
    proxies: __PROXY_NAMES__
    url: 'http://www.gstatic.com/generate_204'
    interval: 300

# Custom rules
rules:
  - DOMAIN-SUFFIX,openai.com,🚀 Auto Select
  - GEOIP,CN,DIRECT
  - MATCH,🚀 Auto Select
```

**Step 2: Assign Template to User**

Edit `users` file and add template filename in the 6th field:

```
uuid|short_id|link_path|comment|groups|mihomo_advanced
xxxxxxxx-1234|abcd1234|user1|Regular User|default,premium|
xxxxxxxx-5678|abcd5678|user2|VIP User|default,vip|advanced-config.yaml
```

**Important Notes:**
- Template filename only (no path): `advanced-config.yaml` not `/templates/advanced-config.yaml`
- Must contain `proxy-template` section (used for server configuration generation)
- Use `__PROXY_NAMES__` placeholder for automatic server list substitution
- If template file not found, falls back to default `mihomo-template.yaml` with warning in logs
- Changes apply immediately (no restart required)

### Use Cases

- **VIP users**: Enhanced DNS, different ports, advanced routing rules
- **Regional users**: Specific geo-routing rules and DNS servers
- **Gaming users**: Low-latency optimized configurations
- **Streaming users**: Optimized for video streaming services
- **Work users**: Limited access to specific domains only

## 🎛️ Custom HTTP Headers

The system supports flexible configuration of custom HTTP headers that are sent with all responses. Headers can be configured to always send or conditionally based on User-Agent matching.

### Configuration Format

Headers are configured via environment variables:
```
CUSTOM_HEADER_<N>=header_name|header_value[|user_agent_regex]
```

**Components:**
- `header_name` - The HTTP header name to send
- `header_value` - The header value (can contain any characters including colons, commas, etc.)
- `user_agent_regex` - (Optional) Regex pattern to match User-Agent header
  - If specified, header is only sent when User-Agent matches (uses `re.search()`)
  - If omitted, header is always sent to all clients

### Examples

**Always send headers (no User-Agent filter):**
```bash
# Profile update interval in hours
CUSTOM_HEADER_1=profile-update-interval|24

# Profile title with base64 encoding
CUSTOM_HEADER_2=profile-title|base64:VGVzdFRpdGxlRXhhbXBsZQ==

# Custom metadata
CUSTOM_HEADER_3=x-server-region|EU
```

**Send header only to specific User-Agents:**
```bash
# Only for Happ clients (User-Agent starts with "Happ/")
CUSTOM_HEADER_4=x-special-feature|enabled|^Happ/\d+\.\d+\.\d+

# Only for mobile clients (User-Agent contains "Mobile", "Android", or "iPhone")
CUSTOM_HEADER_5=x-mobile-config|optimized|Mobile|Android|iPhone

# Only for specific client versions
CUSTOM_HEADER_6=x-new-feature|available|Happ/2\.|Happ/3\.
```

### Features

- **Unlimited headers**: Configure as many custom headers as needed
- **Value flexibility**: Header values can contain any characters (colons, special chars, base64, etc.)
- **Regex matching**: Powerful User-Agent filtering using Python regex (`re.search()`)
- **Pattern matching**: Regex matches anywhere in User-Agent string
- **Validation**: Invalid regex patterns are caught at startup with clear error messages
- **Logging**: Configuration errors are logged for easy debugging

### Use Cases

1. **Client Configuration**: Send update intervals, profile titles, subscription metadata
2. **Feature Flags**: Enable/disable features based on client type or version
3. **A/B Testing**: Send different configurations to different user agents
4. **Mobile Optimization**: Send mobile-specific settings only to mobile clients
5. **Version Control**: Provide version-specific features to compatible clients

### Notes

- Headers are applied to all configuration endpoints (JSON, V2Ray, Mihomo/Clash)
- User-Agent matching is case-sensitive (use `(?i)` in regex for case-insensitive matching)
- Invalid configurations are skipped with warnings in logs
- The pipe character `|` is used as delimiter (more reliable than colon)
- Special routing header for Happ clients is still applied separately for backward compatibility

## API Endpoints

### Get Configuration
```
GET /{secret_path}/{user_link_path}/{format}
```

**Formats:**
- `json` - JSON configuration
- `v2ray` - V2Ray subscription links
- `mihomo` or `clash` - Mihomo/Clash configuration
- `mh`, `clash`, `type3` - Mihomo/Clash Meta YAML

**Examples:**
```
/your_secret_path_here/premium_user1/json
/your_secret_path_here/premium_user1/v2ray
/your_secret_path_here/premium_user1/mh
```

## 🔒 Security Access Control

The service implements strict access control to ensure security:

### Access Rules

The service is accessible **ONLY** from:

1. **Localhost** - Direct connections from `127.0.0.1`, `::1`, or `localhost`
2. **HTTPS Reverse Proxy** - Connections through nginx/reverse proxy with SSL

All other connections will receive a **403 Forbidden** error.

### HTTPS Reverse Proxy Setup

Configure nginx with SSL to access the service securely:

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://unix:/run/sub-stub/sub.stub.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Security Logging

Security events are logged:
- **Allowed connections**: DEBUG level with connection type
- **Blocked connections**: WARNING level with IP and headers
- All blocked attempts are tracked for security monitoring

## Logging

Comprehensive logging system with support for systemd journal integration.

### Configuration via Environment Variables

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=INFO

# Customize log format
export LOG_FORMAT="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
```

### What's Logged

- **Startup events**: Application initialization, configuration loading
- **HTTP requests**: All incoming requests with IP addresses, user agents, status codes
- **Config generation**: User access, format type, IP addresses, groups
- **Access attempts**: Failed authentication attempts with IP tracking
- **Errors**: Server errors, configuration issues, data parsing problems

### Viewing Logs in systemd

```bash
# View real-time logs
journalctl -u sub-stub.service -f

# View last 50 lines
journalctl -u sub-stub.service -n 50

# Filter by log level
journalctl -u sub-stub.service -p warning

# Search by IP address
journalctl -u sub-stub.service | grep "IP: 203.0.113.1"
```

### Log Levels

- **DEBUG**: Detailed information including all requests and internal operations
- **INFO**: General information about successful operations and startup
- **WARNING**: Failed access attempts, security blocks, data issues
- **ERROR**: Server errors and critical problems

## System Integration

### Pre-Start Hook Script

The `scripts/prestart-pip-upgrade.sh` script is designed to run before the service starts (via systemd's `ExecStartPre`).

**Features:**
- Automatically upgrades pip, setuptools, and wheel
- Updates dependencies from `requirements.txt` if available
- Uses file locking to prevent concurrent executions
- Skips upgrades if run within the last 24 hours
- Logs all operations to systemd journal with tag `sub-stub-pip-update`
- Gracefully handles failures without blocking service startup

**Usage:**
The script is called automatically by systemd before the service starts:
```
ExecStartPre=/opt/sub-stub/scripts/prestart-pip-upgrade.sh
```

**View script logs:**
```bash
# View pip upgrade logs
journalctl -t sub-stub-pip-update -f

# View last upgrade attempt
journalctl -t sub-stub-pip-update -n 1
```

## Architecture

### Layered Architecture
1. **Models** - Domain entities and configuration
2. **Repositories** - Data access with caching
3. **Services** - Business logic coordination
4. **Builders** - Configuration generation
5. **Web** - HTTP handlers and routing

### Key Components

**FileCache**: Efficient file caching based on mtime/size
**SpiderXGenerator**: Collision-free spider-x path generation
**GeoFileService**: Geo files update management
**ConfigService**: Configuration building coordination

## Performance Optimizations

- File-based caching with mtime/size tracking
- Lazy loading of configuration files
- Efficient deduplication algorithms
- Minimal memory footprint
- Thread-safe caching

## License

Copyright © 2025. All rights reserved.
