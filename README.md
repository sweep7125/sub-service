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
User database with group-based access control:
```
uuid | short_id | link_path | comment | groups
```
**Example:**
```
xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx | xxxxxxxxxxxxxxxx | premium_user1 | Premium User | premium,vip
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
- `mihomo-template.yaml` - Mihomo YAML configuration template  
- `v2ray-url-template.txt` - VLESS URL template
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

# Optional
export SUBSTUB_CACHE_DIR=/var/cache/sub-stub
export LOG_LEVEL=INFO
export SECRET_PATH=your_secret_path
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
