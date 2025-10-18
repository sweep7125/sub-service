"""Application constants and enumerations."""

from typing import Final

from .config import env_config

# Default profile title (from environment or base64 encoded default)
DEFAULT_PROFILE_TITLE: Final[str] = env_config.profile_title

# Reserved paths that cannot be used as spider-x (includes secret path from env)
RESERVED_PATHS: Final[frozenset[str]] = frozenset(
    {
        env_config.secret_path,
        f"/{env_config.secret_path}",
    }
)

# DNS placeholder strings
DNS_PLACEHOLDERS: Final[frozenset[str]] = frozenset(
    {
        "DNS_PLACEHOLDER",
        "DNS_PLACEHODER",  # Keep typo for backward compatibility
    }
)

# Geo files URLs for automatic updates (from environment)
GEO_FILES_URLS: Final[list[str]] = env_config.geo_files_urls

# HTTP headers (from environment)
PROFILE_UPDATE_INTERVAL: Final[str] = env_config.profile_update_interval
HAPP_ROUTING_FALLBACK: Final[str] = ""

# Spider-X generation parameters (from environment)
SPIDERX_MIN_LENGTH: Final[int] = env_config.spiderx_min_length
SPIDERX_MAX_LENGTH: Final[int] = env_config.spiderx_max_length
SPIDERX_CANDIDATES: Final[list[int]] = [8, 10, 12, 16, 18]
SPIDERX_MAX_ATTEMPTS: Final[int] = 8

# Response MIME types
MIME_TYPE_JSON: Final[str] = "application/json"
MIME_TYPE_YAML: Final[str] = "application/yaml"
MIME_TYPE_TEXT: Final[str] = "text/plain"
