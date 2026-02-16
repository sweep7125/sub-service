"""V2Ray subscription link builder."""

import logging
import urllib.parse
from collections.abc import Callable

from ..models import Server, UserInfo
from ..utils import SpiderXGenerator
from .base import BaseConfigBuilder

logger = logging.getLogger(__name__)


class V2RayBuilder(BaseConfigBuilder):
    """Builder for V2Ray subscription format.

    Generates subscription links in V2Ray's text format where each
    line is a complete vless:// or vmess:// URL.
    """

    def __init__(
        self,
        template_loader: Callable[[], str],
        spiderx_generator: SpiderXGenerator | None = None,
    ) -> None:
        """Initialize V2Ray builder.

        Args:
            template_loader: Function to load URL template
            spiderx_generator: Generator for spider-x paths
        """
        self.template_loader = template_loader
        self.spiderx_generator = spiderx_generator or SpiderXGenerator()

    def build(
        self,
        servers: list[Server],
        user: UserInfo,
    ) -> bytes:
        """Build V2Ray subscription links.

        Args:
            servers: List of available servers
            user: User credentials

        Returns:
            Newline-separated subscription links as bytes
        """
        template = self.template_loader()
        if not template:
            logger.warning("V2Ray template is empty")
            return b""

        template = template.strip()
        eligible = self.get_eligible_servers(servers, user)

        if not eligible:
            logger.warning(f"No eligible servers for user {user.link_path}")
            raise ValueError("User has no access to any servers")

        # Generate links
        links: list[str] = []
        used_paths: set[str] = set()

        for server in eligible:
            spider_x = self.generate_spider_x(server, used_paths, self.spiderx_generator)
            link = self._build_link(template, server, user, spider_x)
            links.append(link)

        return "\n".join(links).encode("utf-8")

    def _build_link(self, template: str, server: Server, user: UserInfo, spider_x: str) -> str:
        """Build a single subscription link from template.

        Args:
            template: URL template with placeholders
            server: Server configuration
            user: User credentials
            spider_x: Spider-X path

        Returns:
            Complete subscription URL
        """
        # URL-encode values
        server_name = urllib.parse.quote(server.server_name, safe="")
        description = urllib.parse.quote(server.description, safe="")
        spider_x_encoded = urllib.parse.quote(spider_x, safe="")

        # Prepare replacements
        replacements = {
            "<ID>": server.fixed_id or user.id,
            "<ADDRESS>": server.host,
            "<SPIDERX>": spider_x_encoded,
            "<SHORTID>": server.fixed_short_id or user.get_short_id(),
            "<SERVERNAME>": server_name,
            "<NAME>": description,
            "<PBK>": server.public_key or "",
        }

        # Apply replacements
        link = template
        for placeholder, value in replacements.items():
            link = link.replace(placeholder, value)

        return link
