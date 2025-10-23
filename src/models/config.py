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
        template_file: Path to V2Ray template
        v2ray_template_file: Path to V2Ray JSON template
        mihomo_template_file: Path to Mihomo YAML template
        happ_routing_file: Path to Happ routing configuration
        cache_dir: Directory for caching data
        geo_cache_ttl: TTL for geo files cache in seconds
    """

    base_dir: Path
    servers_file: Path
    users_file: Path
    template_file: Path
    v2ray_template_file: Path
    mihomo_template_file: Path
    happ_routing_file: Path
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

        # Template files
        templates_dir = base_dir / "templates"
        v2ray_template = templates_dir / "v2ray-template.json"
        mihomo_template = templates_dir / "mihomo-template.yaml"

        config = cls(
            base_dir=base_dir,
            servers_file=env_config.servers_file,
            users_file=env_config.users_file,
            template_file=env_config.template_file,
            v2ray_template_file=v2ray_template,
            mihomo_template_file=mihomo_template,
            happ_routing_file=env_config.happ_routing_file,
            cache_dir=env_config.cache_dir,
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
            (self.template_file, "V2Ray URL template"),
            (self.v2ray_template_file, "V2Ray JSON template"),
            (self.mihomo_template_file, "Mihomo YAML template"),
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
