"""Configuration file repositories."""

import json
from pathlib import Path
from typing import Any

import yaml

from .base import BaseRepository


class JsonConfigRepository(BaseRepository[list[dict[str, Any]]]):
    """Repository for JSON configuration files."""

    def _load_from_file(self, path: Path) -> list[dict[str, Any]]:
        """Load JSON configuration.

        Args:
            path: File path to load from

        Returns:
            List of configuration dictionaries
        """
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
            return data if isinstance(data, list) else []

    def _get_default(self) -> list[dict[str, Any]]:
        """Return empty list if file doesn't exist.

        Returns:
            Empty configuration list
        """
        return []


class YamlConfigRepository(BaseRepository[dict[str, Any]]):
    """Repository for YAML configuration files."""

    def _load_from_file(self, path: Path) -> dict[str, Any]:
        """Load YAML configuration.

        Args:
            path: File path to load from

        Returns:
            Configuration dictionary
        """
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
            return data if isinstance(data, dict) else {}

    def _get_default(self) -> dict[str, Any]:
        """Return empty dict if file doesn't exist.

        Returns:
            Empty configuration dictionary
        """
        return {}


class TextConfigRepository(BaseRepository[str]):
    """Repository for plain text configuration files."""

    def _load_from_file(self, path: Path) -> str:
        """Load text configuration.

        Args:
            path: File path to load from

        Returns:
            File content as string
        """
        with path.open("r", encoding="utf-8") as file:
            return file.read().strip()

    def _get_default(self) -> str:
        """Return empty string if file doesn't exist.

        Returns:
            Empty string
        """
        return ""


class ConfigRepository:
    """Facade for accessing all configuration repositories."""

    def __init__(
        self,
        servers_path: Path,
        users_path: Path,
        template_path: Path,
        v2ray_template_path: Path,
        mihomo_template_path: Path,
    ) -> None:
        """Initialize configuration repositories.

        Args:
            servers_path: Path to servers file (unified format)
            users_path: Path to users file
            template_path: Path to V2Ray URL template file
            v2ray_template_path: Path to V2Ray JSON template file
            mihomo_template_path: Path to Mihomo YAML template file
        """
        from .server_repository import ServerRepository
        from .user_repository import UserRepository

        self.servers = ServerRepository(servers_path)
        self.users = UserRepository(users_path)
        self.template = TextConfigRepository(template_path)
        self.v2ray_template = JsonConfigRepository(v2ray_template_path)
        self.mihomo_template = YamlConfigRepository(mihomo_template_path)
        self._mihomo_template_dir = mihomo_template_path.parent

    def get_all_servers(self):
        """Get all servers from unified configuration.

        Returns:
            List of all servers
        """
        return self.servers.get()

    def get_mihomo_template(self, template_name: str | None = None) -> dict[str, Any]:
        """Load Mihomo template by name.

        Args:
            template_name: Optional custom template filename (e.g., "advanced-config.yaml").
                          If None, returns default mihomo-template.yaml

        Returns:
            Template configuration dictionary
        """
        if not template_name:
            return self.mihomo_template.get()

        # Load custom template
        template_path = self._mihomo_template_dir / template_name
        if not template_path.exists():
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Custom Mihomo template '{template_name}' not found at {template_path}, "
                f"falling back to default template"
            )
            return self.mihomo_template.get()

        # Create temporary repository for custom template
        custom_repo = YamlConfigRepository(template_path)
        return custom_repo.get()
