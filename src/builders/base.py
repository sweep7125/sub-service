"""Base configuration builder interface."""

from typing import Protocol

from ..models import Server, UserInfo


class ConfigBuilder(Protocol):
    """Protocol for configuration builders.

    All builders must implement the build method to generate
    client configuration in their specific format.
    """

    def build(
        self,
        servers: list[Server],
        user: UserInfo,
    ) -> bytes:
        """Build configuration for the given servers and user.

        Args:
            servers: List of available servers
            user: User credentials

        Returns:
            Configuration file content as bytes
        """
        ...


class BaseConfigBuilder:
    """Base class with common functionality for all builders."""

    @staticmethod
    def filter_servers_for_user(servers: list[Server], user: UserInfo) -> list[Server]:
        """Filter servers that are accessible by the given user.

        Uses the new group-based filtering system with legacy support.

        Args:
            servers: List of all servers
            user: User to filter for

        Returns:
            List of accessible servers
        """
        # Filter servers based on group access
        accessible_servers: dict[str, Server] = {}

        for server in servers:
            # Check group access
            if user.has_access_to_groups(server.groups):
                # Use host as unique key to prevent duplicates
                accessible_servers[server.host] = server

        return list(accessible_servers.values())

    @staticmethod
    def deduplicate_by_host(servers: list[Server]) -> list[Server]:
        """Remove duplicate servers with the same host.

        Keeps the first occurrence of each unique host.

        Args:
            servers: List of servers potentially with duplicates

        Returns:
            List of servers with unique hosts
        """
        seen_hosts: set[str] = set()
        unique_servers: list[Server] = []

        for server in servers:
            if server.host not in seen_hosts:
                seen_hosts.add(server.host)
                unique_servers.append(server)

        return unique_servers

    def get_eligible_servers(self, servers: list[Server], user: UserInfo) -> list[Server]:
        """Get eligible servers for user (filtered and deduplicated).

        Args:
            servers: List of all servers
            user: User to get servers for

        Returns:
            List of eligible unique servers
        """
        filtered = self.filter_servers_for_user(servers, user)
        return self.deduplicate_by_host(filtered)
