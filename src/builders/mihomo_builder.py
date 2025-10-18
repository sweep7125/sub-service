"""Mihomo (Clash Meta) configuration builder."""

import copy
import logging
from collections.abc import Callable
from typing import Any

import yaml

from ..models import Server, UserInfo
from .base import BaseConfigBuilder

JsonDict = dict[str, Any]
logger = logging.getLogger(__name__)


class MihomoBuilder(BaseConfigBuilder):
    """Builder for Mihomo/Clash Meta YAML configurations.

    Mihomo is a Clash fork with extended features. This builder
    generates YAML configuration files compatible with Mihomo clients.
    """

    def __init__(self, template_loader: Callable[[], JsonDict] | None = None) -> None:
        """Initialize Mihomo builder.

        Args:
            template_loader: Function to load YAML template
        """
        self.template_loader = template_loader

    def build(
        self,
        servers: list[Server],
        user: UserInfo,
    ) -> bytes:
        """Build Mihomo YAML configuration.

        Args:
            servers: List of available servers
            user: User credentials

        Returns:
            YAML configuration as bytes
        """
        # Load template
        template = self.template_loader() if self.template_loader else {}

        if not isinstance(template, dict):
            logger.error(f"Invalid Mihomo template type: {type(template)}, expected dict")
            raise ValueError("Mihomo template must be a dictionary")

        config = copy.deepcopy(template)

        # Get eligible servers
        eligible = self.get_eligible_servers(servers, user)

        if not eligible:
            logger.warning(f"No eligible servers for user {user.link_path}")
            raise ValueError("User has no access to any servers")

        proxy_names = [server.description for server in eligible]

        # Build proxy configurations
        proxy_template = config.get("proxy-template", {})
        config["proxies"] = [self._build_proxy(proxy_template, server, user) for server in eligible]

        # Remove template from output
        config.pop("proxy-template", None)

        # Substitute proxy names in groups and rules
        for key in ("proxy-groups", "rule-providers", "rules"):
            if key in config:
                config[key] = self._substitute_names(copy.deepcopy(config[key]), proxy_names)

        # Convert to YAML
        yaml_content = yaml.safe_dump(config, sort_keys=False, allow_unicode=True)

        return yaml_content.encode("utf-8")

    def _build_proxy(self, template: JsonDict, server: Server, user: UserInfo) -> JsonDict:
        """Build a single proxy configuration from template.

        Args:
            template: Proxy template configuration
            server: Server to build proxy for
            user: User credentials

        Returns:
            Proxy configuration dictionary
        """
        proxy = copy.deepcopy(template)

        # Set basic proxy parameters
        proxy["name"] = server.description
        proxy["server"] = server.host
        proxy["uuid"] = server.fixed_id or user.id
        proxy["servername"] = server.server_name

        # Set Reality options if present
        reality_opts = proxy.get("reality-opts")
        if isinstance(reality_opts, dict):
            reality_opts["short-id"] = server.fixed_short_id or user.get_short_id()

            if server.public_key:
                reality_opts["public-key"] = server.public_key

        return proxy

    def _substitute_names(self, obj: Any, proxy_names: list[str]) -> Any:
        """Recursively substitute __PROXY_NAMES__ placeholder.

        Args:
            obj: Object to process (dict, list, str, or other)
            proxy_names: List of proxy names to substitute

        Returns:
            Processed object with substitutions
        """
        if isinstance(obj, str):
            # Replace placeholder with proxy names list
            return list(proxy_names) if obj == "__PROXY_NAMES__" else obj

        if isinstance(obj, list):
            result: list[Any] = []
            for item in obj:
                substituted = self._substitute_names(item, proxy_names)

                # Flatten lists (when placeholder was substituted)
                if isinstance(substituted, list):
                    result.extend(substituted)
                else:
                    result.append(substituted)

            return result

        if isinstance(obj, dict):
            return {key: self._substitute_names(value, proxy_names) for key, value in obj.items()}

        return obj
