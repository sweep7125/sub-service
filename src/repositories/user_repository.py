"""User repository for managing user credentials."""

import logging
import uuid
from pathlib import Path

from ..models import UserInfo
from .base import BaseRepository

logger = logging.getLogger(__name__)


def _parse_groups(groups_str: str | None) -> frozenset[str]:
    """Parse comma-separated list of groups.

    Args:
        groups_str: Comma-separated group list

    Returns:
        Frozenset of group names, defaults to {"default"} if empty
    """
    if not groups_str or not groups_str.strip():
        return frozenset(["default"])

    groups = [g.strip() for g in groups_str.split(",")]
    result = frozenset(g for g in groups if g)

    return result if result else frozenset(["default"])


class UserRepository(BaseRepository[dict[str, UserInfo]]):
    """Repository for loading user credentials.

    File format: uuid|short_id|link_path|comment|groups|mihomo_advanced (pipe-separated)
    """

    def _load_from_file(self, path: Path) -> dict[str, UserInfo]:
        """Load users from configuration file.

        Args:
            path: File path to load from

        Returns:
            Dictionary mapping link paths to UserInfo objects
        """
        users: dict[str, UserInfo] = {}

        with path.open("r", encoding="utf-8") as file:
            for line_num, line in enumerate(file, 1):
                stripped = line.strip()

                # Skip empty lines and comments
                if not stripped or stripped.startswith("#"):
                    continue

                try:
                    user = self._parse_line(stripped)
                    if user:
                        key, info = user
                        users[key] = info
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse user line {line_num}: {e}")
                    continue

        return users

    def _parse_line(self, line: str) -> tuple[str, UserInfo] | None:
        """Parse pipe-separated format.

        Format: uuid|short_id|link_path|comment|groups|mihomo_advanced

        Args:
            line: Configuration line

        Returns:
            Tuple of (link_path, UserInfo) or None if invalid
        """
        parts = [p.strip() for p in line.split("|", 5)]

        if len(parts) < 3:
            return None

        user_id = parts[0]
        short_id = parts[1] if len(parts) > 1 else None
        link_path = parts[2] if len(parts) > 2 else None
        comment = parts[3] if len(parts) > 3 else ""
        groups_str = parts[4] if len(parts) > 4 else None
        mihomo_advanced = parts[5] if len(parts) > 5 and parts[5] else None

        if not user_id or not link_path:
            return None

        # Validate UUID format
        try:
            uuid.UUID(user_id)
        except ValueError:
            logger.warning(f"Invalid UUID format for user '{link_path}': {user_id}")
            return None

        groups = _parse_groups(groups_str)

        return link_path, UserInfo(
            id=user_id,
            short_id=short_id or None,
            spider_x=None,
            comment=comment,
            link_path=link_path,
            groups=groups,
            mihomo_advanced=mihomo_advanced,
        )

    def _get_default(self) -> dict[str, UserInfo]:
        """Return empty dict if file doesn't exist.

        Returns:
            Empty user dictionary
        """
        return {}

    def find_by_prefix(self, prefix: str) -> UserInfo | None:
        """Find user by longest matching key prefix.

        Args:
            prefix: Prefix to search for

        Returns:
            UserInfo if found, None otherwise
        """
        if not prefix:
            return None

        users = self.get()
        if not users:
            return None

        # Find the longest key that matches as a prefix
        matching_key = max((key for key in users if prefix.startswith(key)), key=len, default=None)

        return users.get(matching_key) if matching_key else None
