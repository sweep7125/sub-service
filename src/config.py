"""Environment configuration management."""

import logging
import os
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class EnvConfig:
    """Environment configuration loader with validation.

    Loads configuration from environment variables with sensible defaults.
    Supports both .env files and system environment variables.
    """

    def __init__(self) -> None:
        """Initialize configuration from environment."""
        self._load_env_file()

    def _load_env_file(self) -> None:
        """Load .env file if it exists."""
        env_file = Path(__file__).parent.parent / ".env"

        if not env_file.exists():
            return

        try:
            with env_file.open("r", encoding="utf-8") as f:
                for _line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # Skip empty lines and comments
                    if not line or line.startswith("#"):
                        continue

                    # Parse KEY=VALUE
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip()

                        # Don't override existing env vars
                        if key and key not in os.environ:
                            os.environ[key] = value

        except OSError as e:
            logger.warning(f"Failed to load .env file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading .env file: {e}", exc_info=True)

    def get_str(self, key: str, default: str = "") -> str:
        """Get string value from environment.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            String value
        """
        return os.environ.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer value from environment.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Integer value
        """
        value = os.environ.get(key)
        if value is None:
            return default

        try:
            return int(value)
        except ValueError:
            return default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean value from environment.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Boolean value
        """
        value = os.environ.get(key)
        if value is None:
            return default

        return value.lower() in ("true", "yes", "1", "on")

    def get_path(self, key: str, default: Path | None = None) -> Path | None:
        """Get path value from environment.

        Args:
            key: Environment variable name
            default: Default value if not set

        Returns:
            Path object or None
        """
        value = os.environ.get(key)
        if value is None:
            return default

        return Path(value)

    def get_list(
        self, key: str, default: list[str] | None = None, separator: str = ","
    ) -> list[str]:
        """Get list value from environment.

        Args:
            key: Environment variable name
            default: Default value if not set
            separator: List item separator

        Returns:
            List of strings
        """
        value = os.environ.get(key)
        if value is None:
            return default or []

        return [item.strip() for item in value.split(separator) if item.strip()]

    # Security settings
    @property
    def secret_path(self) -> str:
        """Get secret API path."""
        value = self.get_str("SECRET_PATH")
        if not value:
            raise ValueError("SECRET_PATH environment variable is required for security")
        return value

    # Server settings
    @property
    def socket_path(self) -> str | None:
        """Get Unix socket path for production."""
        value = self.get_str("SOCK")
        return value if value else None

    @property
    def dev_host(self) -> str:
        """Get development server host."""
        return self.get_str("DEV_HOST", "127.0.0.1")

    @property
    def dev_port(self) -> int:
        """Get development server port."""
        return self.get_int("DEV_PORT", 5000)

    @property
    def dev_debug(self) -> bool:
        """Get development debug mode."""
        return self.get_bool("DEV_DEBUG", True)

    # Path settings
    @property
    def base_dir(self) -> Path:
        """Get base directory."""
        custom_path = self.get_path("BASE_DIR")
        if custom_path:
            return custom_path
        return Path(__file__).parent.parent

    @property
    def cache_dir(self) -> Path:
        """Get cache directory."""
        return self.get_path("SUBSTUB_CACHE_DIR") or Path("/var/cache/sub-stub")

    @property
    def servers_file(self) -> Path:
        """Get servers file path (unified format)."""
        custom = self.get_str("SERVERS_FILE", "servers")
        path = Path(custom)
        return path if path.is_absolute() else self.base_dir / path

    @property
    def users_file(self) -> Path:
        """Get users file path."""
        custom = self.get_str("USERS_FILE", "users")
        path = Path(custom)
        return path if path.is_absolute() else self.base_dir / path

    @property
    def template_file(self) -> Path:
        """Get V2Ray URL template file path."""
        # Support legacy TEMPLATE_FILE env var
        custom = self.get_str("TEMPLATE_FILE", "templates/v2ray-url-template.txt")
        path = Path(custom)
        return path if path.is_absolute() else self.base_dir / path

    @property
    def happ_routing_file(self) -> Path:
        """Get Happ routing file path."""
        custom = self.get_str("HAPP_ROUTING_FILE", "happ.routing")
        path = Path(custom)
        return path if path.is_absolute() else self.base_dir / path

    # Cache settings
    @property
    def geo_cache_ttl(self) -> int:
        """Get geo cache TTL in seconds."""
        return self.get_int("GEO_CACHE_TTL", 600)

    @property
    def enable_file_cache(self) -> bool:
        """Check if file cache is enabled."""
        return self.get_bool("ENABLE_FILE_CACHE", True)

    # Geo files settings
    @property
    def geo_files_urls(self) -> list[str]:
        """Get geo files URLs."""
        urls = self.get_list("GEO_FILES_URLS")
        if urls:
            return urls

        # Default URLs
        return [
            "https://raw.githubusercontent.com/sweep7125/rulesets/refs/heads/xray-rulesets/geosite.dat",
            "https://raw.githubusercontent.com/sweep7125/rulesets/refs/heads/xray-rulesets/geoip.dat",
        ]

    # Logging settings
    @property
    def log_level(self) -> str:
        """Get log level."""
        return self.get_str("LOG_LEVEL", "INFO").upper()

    @property
    def log_format(self) -> str:
        """Get log format."""
        return self.get_str("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Advanced settings
    @property
    def spiderx_min_length(self) -> int:
        """Get minimum Spider-X path length."""
        return self.get_int("SPIDERX_MIN_LENGTH", 10)

    @property
    def spiderx_max_length(self) -> int:
        """Get maximum Spider-X path length."""
        return self.get_int("SPIDERX_MAX_LENGTH", 24)

    @property
    def flask_json_sort_keys(self) -> bool:
        """Get Flask JSON sort keys setting."""
        return self.get_bool("FLASK_JSON_SORT_KEYS", False)

    @property
    def worker_threads(self) -> int:
        """Get number of worker threads."""
        return self.get_int("WORKER_THREADS", 1)

    @property
    def custom_headers(self) -> list[dict[str, str]]:
        """Get custom headers configuration.

        Parses all CUSTOM_HEADER_* environment variables.
        Format: CUSTOM_HEADER_<N>=header_name|header_value[|user_agent_regex]

        The pipe character (|) is used as delimiter between fields.

        Returns:
            List of dictionaries with keys:
            - name: Header name
            - value: Header value
            - user_agent_regex: Optional regex pattern for User-Agent filtering
        """
        headers = []

        # Collect all CUSTOM_HEADER_* environment variables
        for key, value in os.environ.items():
            if not key.startswith("CUSTOM_HEADER_"):
                continue

            # Parse header configuration: header_name|header_value[|user_agent_regex]
            parts = value.split("|", 2)  # Split into max 3 parts
            if len(parts) < 2:
                logger.warning(f"Invalid custom header format in {key}: {value}")
                continue

            header_name = parts[0].strip()
            header_value = parts[1].strip()
            user_agent_regex = parts[2].strip() if len(parts) > 2 else None

            if not header_name or not header_value:
                logger.warning(f"Empty header name or value in {key}: {value}")
                continue

            # Validate regex if provided
            if user_agent_regex:
                try:
                    re.compile(user_agent_regex)
                except re.error as e:
                    logger.error(f"Invalid regex in {key}: {user_agent_regex} - {e}")
                    continue

            headers.append(
                {
                    "name": header_name,
                    "value": header_value,
                    "user_agent_regex": user_agent_regex,
                }
            )

        return headers


# Global configuration instance
env_config = EnvConfig()
