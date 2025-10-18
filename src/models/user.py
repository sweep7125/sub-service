"""User model definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class UserInfo:
    """Represents a user with their VPN/Proxy credentials.

    Attributes:
        id: User's UUID for VPN connection
        short_id: Short ID for Reality protocol
        spider_x: Spider-X path for additional obfuscation
        comment: Human-readable comment/name for the user
        link_path: Custom path component for user's subscription link
        groups: Set of group names the user belongs to
    """

    id: str
    short_id: str | None = None
    spider_x: str | None = None
    comment: str = ""
    link_path: str = ""
    groups: frozenset[str] = frozenset()

    def get_short_id(self, default: str = "") -> str:
        """Get short ID with fallback.

        Args:
            default: Default value if short_id is None

        Returns:
            Short ID or default value
        """
        return self.short_id or default

    def is_in_group(self, group: str) -> bool:
        """Check if user belongs to a specific group.

        Args:
            group: Group name to check

        Returns:
            True if user is in the group, False otherwise
        """
        return group in self.groups

    def has_access_to_groups(self, server_groups: frozenset[str]) -> bool:
        """Check if user has access to any of the server's groups.

        Args:
            server_groups: Set of groups the server belongs to

        Returns:
            True if user and server share at least one group
        """
        # If server has no groups, it's available to everyone
        if not server_groups:
            return True
        # If user has no groups, they can't access group-restricted servers
        if not self.groups:
            return False
        # Check for intersection
        return bool(self.groups & server_groups)
