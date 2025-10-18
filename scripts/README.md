# System Integration Scripts

This directory contains scripts for integrating the service with systemd and other system components.

## prestart-pip-upgrade.sh

Pre-start hook script for systemd service that manages Python package upgrades.

### Purpose

Automatically upgrades pip dependencies before the service starts, ensuring that:
- Python packaging tools (pip, setuptools, wheel) are up to date
- Application dependencies are upgraded to their latest versions (if `requirements.txt` exists)
- Upgrades happen safely without affecting service startup on failure

### Features

- **Automatic Dependency Management**: Upgrades packages from `requirements.txt` using `--upgrade-strategy only-if-needed`
- **File Locking**: Uses `flock` to prevent concurrent upgrades from multiple service instances
- **24-Hour Cache**: Skips upgrades if the script has run within the last 24 hours
- **Systemd Integration**: Logs all operations to systemd journal for easy monitoring
- **Graceful Failure Handling**: Non-fatal failures don't block service startup
- **Detailed Logging**: Reports outdated packages before and after upgrades

### Configuration

The script respects these environment variables:

- `SUBSTUB_CACHE_DIR` - Cache directory for upgrade tracking (default: `/var/cache/sub-stub`)
- `VENV` - Python virtual environment path (must match `.venv` location)
- `REQ` - Path to `requirements.txt` file

### Usage

#### Automatic (via systemd)

The script runs automatically before service startup when configured in `sub-stub.service`:

```ini
ExecStartPre=/opt/sub-stub/scripts/prestart-pip-upgrade.sh
```

#### Manual Execution

You can also run the script manually for testing or forcing an upgrade:

```bash
# Make script executable
chmod +x ./scripts/prestart-pip-upgrade.sh

# Run manually
./scripts/prestart-pip-upgrade.sh
```

### Monitoring

#### View Logs

```bash
# View all pip upgrade logs
journalctl -t sub-stub-pip-update -f

# View last 10 upgrade attempts
journalctl -t sub-stub-pip-update -n 10

# View logs for a specific date
journalctl -t sub-stub-pip-update --since "2025-10-18"

# View only warning/error logs
journalctl -t sub-stub-pip-update -p warning
```

#### Log Messages

- `"skip: <24h"` - Upgrade skipped (ran within last 24 hours)
- `"no outdated before"` - No outdated packages detected
- `"outdated before: X -> package1 package2"` - Found X outdated packages
- `"updated: Y -> package1 package2"` - Successfully updated Y packages
- `"no updates needed"` - All packages are up to date
- `"no changes (pinned/constraints)"` - Upgrade attempted but no packages changed (likely pinned versions)

### Script Logic

1. Create/acquire file lock in cache directory
2. Check if last upgrade was within 24 hours
3. If not, get list of outdated packages
4. Upgrade pip, setuptools, wheel
5. If `requirements.txt` exists, upgrade dependencies from it
6. Compare before/after lists and report changes
7. Update timestamp for next 24-hour check
8. Release lock

### Error Handling

The script includes graceful error handling:

- **Lock failures**: Script logs warning but continues (allows skipping on lock timeout)
- **pip failures**: Logged as warnings but don't block service startup
- **Missing `requirements.txt`**: Falls back to updating only explicitly outdated packages
- **JSON parsing errors**: Handled gracefully, defaults to empty list

### Performance Considerations

- **Network calls**: Only made once per 24 hours (when upgrade runs)
- **Timeouts**: Each pip call has 15-second timeout to prevent hanging
- **Cache usage**: Disabled for pip to ensure fresh package metadata
- **Execution time**: Typically 5-30 seconds depending on number of updates

### Requirements

- Bash with `set -Eeuo pipefail` support
- Python 3 with pip
- `flock` utility for file locking (part of `util-linux`)
- `logger` command for systemd logging
- Writable cache directory at `$SUBSTUB_CACHE_DIR`
