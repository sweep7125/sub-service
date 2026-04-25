"""Configuration file repositories."""

import json
import logging
from pathlib import Path
from typing import Any

import yaml

from .base import BaseRepository

logger = logging.getLogger(__name__)


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
        v2ray_profile_path: Path,
        xray_profile_path: Path,
        mihomo_profile_path: Path,
    ) -> None:
        """Initialize configuration repositories.

        Args:
            servers_path: Path to servers file (unified format)
            users_path: Path to users file
            v2ray_profile_path: Path to V2Ray subscription base file
            xray_profile_path: Path to Xray JSON base file
            mihomo_profile_path: Path to Mihomo YAML base file
        """
        from .server_repository import ServerRepository
        from .user_repository import UserRepository

        self.servers = ServerRepository(servers_path)
        self.users = UserRepository(users_path)
        self.v2ray_profile = TextConfigRepository(v2ray_profile_path)
        self.xray_profile = JsonConfigRepository(xray_profile_path)
        self.mihomo_profile = YamlConfigRepository(mihomo_profile_path)
        self._profile_repositories: dict[Path, BaseRepository[Any]] = {
            v2ray_profile_path: self.v2ray_profile,
            xray_profile_path: self.xray_profile,
            mihomo_profile_path: self.mihomo_profile,
        }

    def get_all_servers(self):
        """Get all servers from unified configuration.

        Returns:
            List of all servers
        """
        return self.servers.get()

    def get_v2ray_template(self, user_agent: str = "") -> str:
        """Load V2Ray subscription base file with optional UA variant."""
        return self._load_profile(self.v2ray_profile.file_path, TextConfigRepository, user_agent)

    def get_xray_template(self, user_agent: str = "") -> list[dict[str, Any]]:
        """Load Xray JSON base file with optional UA variant."""
        return self._load_profile(self.xray_profile.file_path, JsonConfigRepository, user_agent)

    def get_mihomo_template(
        self, template_name: str | None = None, user_agent: str = ""
    ) -> dict[str, Any]:
        """Load Mihomo base file by exact name or UA variant.

        Args:
            template_name: Optional exact template filename override
            user_agent: Request User-Agent for keyword profile selection

        Returns:
            Template configuration dictionary
        """
        return self._load_profile(
            self.mihomo_profile.file_path,
            YamlConfigRepository,
            user_agent,
            profile_name=template_name,
        )

    def _load_profile(
        self,
        base_path: Path,
        repository_type: type[BaseRepository[Any]],
        user_agent: str = "",
        profile_name: str | None = None,
    ) -> Any:
        """Load base or keyword-specific profile content."""
        profile_path = self._resolve_profile_path(base_path, user_agent, profile_name)
        repository = self._get_repository(profile_path, repository_type)
        return repository.get()

    def _get_repository(
        self, path: Path, repository_type: type[BaseRepository[Any]]
    ) -> BaseRepository[Any]:
        """Get cached repository instance for file path."""
        repository = self._profile_repositories.get(path)
        if repository is None:
            repository = repository_type(path)
            self._profile_repositories[path] = repository
        return repository

    def _resolve_profile_path(
        self, base_path: Path, user_agent: str, profile_name: str | None = None
    ) -> Path:
        """Resolve exact profile or best UA-matched variant."""
        if profile_name:
            profile_path = base_path.parent / profile_name
            if profile_path.exists():
                return profile_path

            logger.warning(
                f"Custom profile '{profile_name}' not found at {profile_path}, "
                f"falling back to User-Agent selection for {base_path.name}"
            )

        return self._select_user_agent_profile(base_path, user_agent)

    def _select_user_agent_profile(self, base_path: Path, user_agent: str) -> Path:
        """Select best profile variant for request User-Agent."""
        normalized_ua = user_agent.casefold().strip()
        if not normalized_ua:
            return base_path

        prefix = f"{base_path.stem}_"

        try:
            candidates = sorted(base_path.parent.iterdir(), key=lambda path: path.name)
        except FileNotFoundError:
            return base_path

        matches: list[tuple[int, int, int, str, Path]] = []
        for path in candidates:
            if not path.is_file() or path.suffix != base_path.suffix:
                continue
            if not path.stem.startswith(prefix):
                continue

            keywords = self._extract_profile_keywords(path, base_path.stem)
            matched_scores = [
                (normalized_ua.find(keyword), -len(keyword))
                for keyword in keywords
                if keyword in normalized_ua
            ]
            if not matched_scores:
                continue

            best_match = min(matched_scores)
            matches.append((best_match[0], best_match[1], len(keywords), path.name, path))

        return min(matches)[4] if matches else base_path

    def _extract_profile_keywords(self, path: Path, base_name: str) -> tuple[str, ...]:
        """Extract OR-matched keywords from profile filename."""
        stem = path.stem
        if stem == base_name or not stem.startswith(f"{base_name}_"):
            return ()

        suffix = stem[len(base_name) + 1 :]
        return tuple(part.casefold() for part in suffix.split("_") if part)
