"""Server model definitions."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Server:
    """Represents a VPN/Proxy server configuration.

    Attributes:
        host: Server hostname or IP address
        description: Human-readable server description
        alias: Alternative name for the server (used as SNI)
        dns_override: Custom DNS server address
        public_key: Public key for authentication (Reality)
        fixed_id: Fixed UUID for external servers
        fixed_short_id: Fixed short ID for external servers
        is_external: Whether this is an external (shared) server
        groups: Set of group names this server belongs to
    """

    host: str
    description: str
    alias: str | None = None
    dns_override: str | None = None
    public_key: str | None = None
    fixed_id: str | None = None
    fixed_short_id: str | None = None
    is_external: bool = False
    groups: frozenset[str] = frozenset()

    def is_in_group(self, group: str) -> bool:
        """Check if server belongs to a specific group.

        Args:
            group: Group name to check

        Returns:
            True if server is in the group, False otherwise
        """
        return group in self.groups

    @property
    def server_name(self) -> str:
        """Get the server name to use for SNI.

        Returns:
            Server alias if available, otherwise host
        """
        return self.alias or self.host
