"""Application configuration model."""

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppConfig:
    """Application configuration settings.

    Attributes:
        base_dir: Base directory of the application
        servers_file: Path to servers configuration (unified format)
        users_file: Path to users configuration
        v2ray_profile_file: Path to V2Ray subscription base file
        xray_profile_file: Path to Xray JSON base file
        mihomo_profile_file: Path to Mihomo YAML base file
        happ_routing_file: Path to Happ routing configuration
        incy_routing_file: Path to Incy routing configuration
        cache_dir: Directory for caching data
        geo_cache_ttl: TTL for geo files cache in seconds
    """

    base_dir: Path
    servers_file: Path
    users_file: Path
    v2ray_profile_file: Path
    xray_profile_file: Path
    mihomo_profile_file: Path
    happ_routing_file: Path
    incy_routing_file: Path
    cache_dir: Path
    geo_cache_ttl: int = 600

    @classmethod
    def from_environment(cls, base_dir: Path | None = None) -> "AppConfig":
        """Create configuration from environment variables.

        Uses the EnvConfig class to load settings from .env file and environment.

        Args:
            base_dir: Override base directory (for testing)

        Returns:
            AppConfig instance

        Raises:
            FileNotFoundError: If required configuration files are missing
        """
        from ..config import env_config

        # Use provided base_dir or get from environment
        if base_dir is None:
            base_dir = env_config.base_dir

        config = cls(
            base_dir=base_dir,
            servers_file=env_config.resolve_path("SERVERS_FILE", "servers", base_dir),
            users_file=env_config.resolve_path("USERS_FILE", "users", base_dir),
            v2ray_profile_file=env_config.resolve_profile_path(
                "V2RAY_TEMPLATE_FILE",
                "templates/v2ray.lst",
                base_dir,
                legacy_key="TEMPLATE_FILE",
                legacy_default="templates/v2ray-url-template.txt",
            ),
            xray_profile_file=env_config.resolve_profile_path(
                "XRAY_TEMPLATE_FILE",
                "templates/xray.json",
                base_dir,
                legacy_default="templates/v2ray-template.json",
            ),
            mihomo_profile_file=env_config.resolve_profile_path(
                "MIHOMO_TEMPLATE_FILE",
                "templates/mihomo.yaml",
                base_dir,
                legacy_default="templates/mihomo-template.yaml",
            ),
            happ_routing_file=env_config.resolve_path("HAPP_ROUTING_FILE", "happ.routing", base_dir),
            incy_routing_file=env_config.resolve_path("INCY_ROUTING_FILE", "incy.routing", base_dir),
            cache_dir=env_config.resolve_path("SUBSTUB_CACHE_DIR", "/var/cache/sub-stub", base_dir),
            geo_cache_ttl=env_config.geo_cache_ttl,
        )

        # Validate required files exist
        config._validate_required_files()

        return config

    def _validate_required_files(self) -> None:
        """Validate that required configuration files exist.

        Raises:
            FileNotFoundError: If any required file is missing
        """
        required_files = [
            (self.servers_file, "servers configuration"),
            (self.users_file, "users configuration"),
            (self.v2ray_profile_file, "V2Ray subscription base file"),
            (self.xray_profile_file, "Xray JSON base file"),
            (self.mihomo_profile_file, "Mihomo YAML base file"),
        ]

        missing = []
        for file_path, description in required_files:
            if not file_path.exists():
                missing.append(f"{description}: {file_path}")

        if missing:
            raise FileNotFoundError(
                "Required configuration files are missing:\n"
                + "\n".join(f"  - {m}" for m in missing)
            )
