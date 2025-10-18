"""Server repository for managing server configurations."""

from pathlib import Path

from ..models import Server
from ..utils import decode_unicode_escapes
from .base import BaseRepository


def _parse_groups(groups_str: str | None) -> frozenset[str]:
    """Parse comma-separated list of groups.

    Args:
        groups_str: Comma-separated group list

    Returns:
        Frozenset of group names (empty set if no groups specified)
    """
    if not groups_str or not groups_str.strip():
        return frozenset()

    groups = [g.strip() for g in groups_str.split(",")]
    return frozenset(g for g in groups if g)


class ServerRepository(BaseRepository[list[Server]]):
    """Repository for loading server configurations.

    File format: host|sni|dns|public_key|description|groups|type|uuid|short_id
    """

    def __init__(self, file_path: Path) -> None:
        """Initialize server repository.

        Args:
            file_path: Path to servers configuration file
        """
        super().__init__(file_path)

    def _load_from_file(self, path: Path) -> list[Server]:
        """Load servers from configuration file.

        Args:
            path: File path to load from

        Returns:
            List of Server objects
        """
        servers: list[Server] = []

        with path.open("r", encoding="utf-8") as file:
            for line in file:
                stripped = line.strip()

                # Skip empty lines and comments
                if not stripped or stripped.startswith("#"):
                    continue

                server = self._parse_line(stripped)
                if server:
                    servers.append(server)

        return servers

    def _parse_line(self, line: str) -> Server | None:
        """Parse new pipe-separated format.

        Format: host|sni|dns|public_key|description|groups|type|uuid|short_id

        Args:
            line: Configuration line

        Returns:
            Server object or None if invalid
        """
        parts = [p.strip() for p in line.split("|", 8)]

        if len(parts) < 5:
            return None

        host = parts[0]
        sni = parts[1] if len(parts) > 1 else None
        dns = parts[2] if len(parts) > 2 else None
        public_key = parts[3] if len(parts) > 3 else None
        description = parts[4] if len(parts) > 4 else host
        groups_str = parts[5] if len(parts) > 5 else None
        server_type = parts[6].lower() if len(parts) > 6 and parts[6] else "internal"
        fixed_id = parts[7] if len(parts) > 7 and parts[7] else None
        fixed_short_id = parts[8] if len(parts) > 8 and parts[8] else None

        if not host:
            return None

        # Decode unicode escapes in description and sni
        description = decode_unicode_escapes(description) if description else host
        sni = decode_unicode_escapes(sni) if sni else None

        # Parse groups
        groups = _parse_groups(groups_str)

        # Determine if external
        is_external = server_type == "external"

        return Server(
            host=host,
            description=description,
            alias=sni or host,
            dns_override=dns,
            public_key=public_key,
            fixed_id=fixed_id,
            fixed_short_id=fixed_short_id,
            is_external=is_external,
            groups=groups,
        )

    def _get_default(self) -> list[Server]:
        """Return empty list if file doesn't exist.

        Returns:
            Empty server list
        """
        return []
