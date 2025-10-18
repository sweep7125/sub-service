"""Legacy JSON configuration builder for older V2Ray clients."""

import copy
import json
import logging
from collections.abc import Callable
from typing import Any

from ..constants import DNS_PLACEHOLDERS
from ..models import Server, UserInfo
from ..utils import SpiderXGenerator
from .base import BaseConfigBuilder

JsonDict = dict[str, Any]
logger = logging.getLogger(__name__)


class LegacyJsonBuilder(BaseConfigBuilder):
    """Builder for legacy V2Ray JSON configuration format.

    Generates multiple JSON configuration blocks, one per server,
    in the format expected by older V2Ray-based clients.
    """

    def __init__(
        self,
        json_loader: Callable[[], list[dict]],
        spiderx_generator: SpiderXGenerator | None = None,
    ) -> None:
        """Initialize legacy JSON builder.

        Args:
            json_loader: Function to load JSON template blocks
            spiderx_generator: Generator for spider-x paths
        """
        self.json_loader = json_loader
        self.spiderx_generator = spiderx_generator or SpiderXGenerator()

    def build(
        self,
        servers: list[Server],
        user: UserInfo,
    ) -> bytes:
        """Build legacy JSON configuration.

        Args:
            servers: List of available servers
            user: User credentials

        Returns:
            JSON array of configuration blocks as bytes
        """
        base_blocks = self.json_loader() or []
        if not isinstance(base_blocks, list):
            logger.warning(f"Invalid JSON template type: {type(base_blocks)}, expected list")
            base_blocks = []

        eligible = self.get_eligible_servers(servers, user)

        if not eligible:
            logger.warning(f"No eligible servers for user {user.link_path}")
            raise ValueError("User has no access to any servers")

        # Build configuration blocks
        configurations: list[JsonDict] = []
        used_paths: set[str] = set()

        for server in eligible:
            spider_x = self._generate_spider_x(server, used_paths)

            # Create one config block per template per server
            for template_block in base_blocks:
                config = self._build_config_block(template_block, server, user, spider_x)
                configurations.append(config)

        return json.dumps(configurations, ensure_ascii=False, indent=2).encode("utf-8")

    def _generate_spider_x(self, server: Server, used_paths: set[str]) -> str:
        """Generate unique spider-x path for non-external servers.

        Args:
            server: Server to generate path for
            used_paths: Set of already used paths

        Returns:
            Spider-x path or empty string for external servers
        """
        if server.is_external:
            return ""

        # Try to generate unique path
        for _ in range(8):
            path = self.spiderx_generator.generate()
            if path not in used_paths:
                used_paths.add(path)
                return path

        return ""

    def _build_config_block(
        self, template: JsonDict, server: Server, user: UserInfo, spider_x: str
    ) -> JsonDict:
        """Build a single configuration block from template.

        Args:
            template: Template configuration block
            server: Server configuration
            user: User credentials
            spider_x: Spider-X path

        Returns:
            Configuration block dictionary
        """
        config = copy.deepcopy(template)

        # Update remarks
        original_remarks = config.get("remarks", "")
        config["remarks"] = f"{server.description} | {original_remarks}"

        # Apply DNS overrides
        self._apply_dns_override(config, server.dns_override)

        # Patch outbound configurations
        self._patch_outbounds(config, server, user, spider_x)

        return config

    def _apply_dns_override(self, config: JsonDict, dns_override: str | None) -> None:
        """Apply DNS override to configuration.

        Args:
            config: Configuration to modify
            dns_override: DNS server address or None
        """
        if not dns_override:
            return

        dns_config = config.get("dns")
        if not isinstance(dns_config, dict):
            return

        servers = dns_config.get("servers")
        if not isinstance(servers, list):
            return

        # Replace DNS placeholders
        dns_config["servers"] = [
            dns_override if (isinstance(s, str) and s in DNS_PLACEHOLDERS) else s for s in servers
        ]

    def _patch_outbounds(
        self, config: JsonDict, server: Server, user: UserInfo, spider_x: str
    ) -> None:
        """Patch outbound configurations with server details.

        Args:
            config: Configuration to modify
            server: Server configuration
            user: User credentials
            spider_x: Spider-X path
        """
        outbounds = config.get("outbounds")
        if not isinstance(outbounds, list):
            return

        for outbound in outbounds:
            self._patch_outbound(outbound, server, user, spider_x)

    def _patch_outbound(
        self, outbound: JsonDict, server: Server, user: UserInfo, spider_x: str
    ) -> None:
        """Patch a single outbound configuration.

        Args:
            outbound: Outbound configuration to modify
            server: Server configuration
            user: User credentials
            spider_x: Spider-X path
        """
        # Patch settings/vnext
        settings = outbound.get("settings")
        if isinstance(settings, dict):
            vnext_list = settings.get("vnext")
            if isinstance(vnext_list, list):
                for vnext in vnext_list:
                    self._patch_vnext(vnext, server, user)

        # Patch stream settings for Reality
        stream_settings = outbound.get("streamSettings")
        if isinstance(stream_settings, dict):
            self._patch_reality_settings(stream_settings, server, user, spider_x)

    def _patch_vnext(self, vnext: JsonDict, server: Server, user: UserInfo) -> None:
        """Patch vnext configuration.

        Args:
            vnext: Vnext configuration to modify
            server: Server configuration
            user: User credentials
        """
        # Patch user IDs
        users = vnext.get("users")
        if isinstance(users, list):
            for user_config in users:
                if isinstance(user_config, dict):
                    user_config["id"] = server.fixed_id or user.id

        # Patch address
        address = vnext.get("address")
        if not address or str(address).lower() == "null":
            vnext["address"] = server.host

    def _patch_reality_settings(
        self, stream_settings: JsonDict, server: Server, user: UserInfo, spider_x: str
    ) -> None:
        """Patch Reality protocol settings.

        Args:
            stream_settings: Stream settings to modify
            server: Server configuration
            user: User credentials
            spider_x: Spider-X path
        """
        security = str(stream_settings.get("security", "")).lower()
        if security != "reality":
            return

        reality_settings = stream_settings.get("realitySettings")
        if not isinstance(reality_settings, dict):
            return

        # Set server name
        if server.alias:
            reality_settings["serverName"] = server.alias

        # Set short ID
        reality_settings["shortId"] = server.fixed_short_id or user.get_short_id()

        # Set spider-X (empty for external servers)
        reality_settings["spiderX"] = "" if server.is_external else spider_x

        # Set public key (password)
        if server.public_key:
            reality_settings["password"] = server.public_key
