"""Configuration service for managing builders and repositories."""

from ..builders import LegacyJsonBuilder, MihomoBuilder, V2RayBuilder
from ..models import AppConfig, Server, UserInfo
from ..repositories import ConfigRepository
from ..utils import SpiderXGenerator


class ConfigService:
    """Service for generating VPN/Proxy configurations.

    Coordinates between repositories and builders to generate
    configurations in various formats.
    """

    def __init__(self, config: AppConfig) -> None:
        """Initialize configuration service.

        Args:
            config: Application configuration
        """
        self.config = config

        # Initialize repositories
        self.repos = ConfigRepository(
            servers_path=config.servers_file,
            users_path=config.users_file,
            template_path=config.template_file,
            v2ray_template_path=config.v2ray_template_file,
            mihomo_template_path=config.mihomo_template_file,
        )

        # Initialize spider-x generator
        self.spiderx_gen = SpiderXGenerator()

        # Initialize builders
        self.mihomo_builder = MihomoBuilder(template_loader=self.repos.mihomo_template.get)

        self.v2ray_builder = V2RayBuilder(
            template_loader=self.repos.template.get,
            spiderx_generator=self.spiderx_gen,
        )

        self.legacy_builder = LegacyJsonBuilder(
            json_loader=self.repos.v2ray_template.get,
            spiderx_generator=self.spiderx_gen,
        )

    def get_servers(self) -> list[Server]:
        """Get all available servers.

        Returns:
            List of all servers
        """
        return self.repos.get_all_servers()

    def find_user(self, prefix: str) -> UserInfo | None:
        """Find user by key prefix.

        Args:
            prefix: User key prefix

        Returns:
            UserInfo if found, None otherwise
        """
        return self.repos.users.find_by_prefix(prefix)

    def build_mihomo_config(self, servers: list[Server], user: UserInfo) -> bytes:
        """Build Mihomo/Clash configuration.

        Args:
            servers: Available servers
            user: User credentials

        Returns:
            YAML configuration
        """
        return self.mihomo_builder.build(servers, user)

    def build_v2ray_config(self, servers: list[Server], user: UserInfo) -> bytes:
        """Build V2Ray subscription.

        Args:
            servers: Available servers
            user: User credentials

        Returns:
            V2Ray subscription links
        """
        return self.v2ray_builder.build(servers, user)

    def build_legacy_config(self, servers: list[Server], user: UserInfo) -> bytes:
        """Build legacy JSON configuration.

        Args:
            servers: Available servers
            user: User credentials

        Returns:
            JSON configuration
        """
        return self.legacy_builder.build(servers, user)
