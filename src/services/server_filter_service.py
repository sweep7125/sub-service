"""Service for filtering servers based on user groups."""

from collections.abc import Iterable

from ..models import Server, UserInfo


def filter_servers_by_groups(
    servers: Iterable[Server],
    user: UserInfo,
) -> list[Server]:
    """Filter servers that user has access to based on groups.

    Rules:
    1. If server has no groups (empty set), it's available to everyone
    2. If server has groups, user must have at least one matching group
    3. Duplicates are removed (same server in multiple groups)

    Args:
        servers: Iterable of Server objects
        user: UserInfo object with user's groups

    Returns:
        List of unique Server objects the user can access
    """
    accessible_servers: dict[str, Server] = {}

    for server in servers:
        # Check group access
        if user.has_access_to_groups(server.groups):
            # Use host as unique key to prevent duplicates
            accessible_servers[server.host] = server

    return list(accessible_servers.values())


def get_servers_for_user(
    all_servers: list[Server],
    user: UserInfo,
    *,
    sort_by_description: bool = True,
) -> list[Server]:
    """Get all servers accessible to a user with optional sorting.

    Args:
        all_servers: List of all available servers
        user: UserInfo object
        sort_by_description: Whether to sort servers by description

    Returns:
        List of accessible Server objects
    """
    filtered = filter_servers_by_groups(all_servers, user)

    if sort_by_description:
        filtered.sort(key=lambda s: s.description)

    return filtered


def get_user_groups_summary(user: UserInfo) -> str:
    """Get human-readable summary of user's groups.

    Args:
        user: UserInfo object

    Returns:
        Comma-separated list of groups or "default"
    """
    if not user.groups:
        return "default"

    return ", ".join(sorted(user.groups))


def get_server_groups_summary(server: Server) -> str:
    """Get human-readable summary of server's groups.

    Args:
        server: Server object

    Returns:
        Comma-separated list of groups or "all" if no groups
    """
    if not server.groups:
        return "all"

    return ", ".join(sorted(server.groups))
