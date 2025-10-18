"""Spider-X path generator for obfuscation."""

import logging
import random
import secrets

from ..constants import (
    RESERVED_PATHS,
    SPIDERX_CANDIDATES,
    SPIDERX_MAX_LENGTH,
    SPIDERX_MIN_LENGTH,
)

logger = logging.getLogger(__name__)


class SpiderXGenerator:
    """Generates random spider-x paths for VPN obfuscation.

    Spider-X paths are used in Reality protocol to add additional
    layer of obfuscation by randomizing the path component.
    """

    def __init__(self, max_cache_size: int = 10000) -> None:
        """Initialize generator with empty collision tracking.

        Args:
            max_cache_size: Maximum number of paths to cache before clearing
        """
        self._used_paths: set[str] = set()
        self._max_cache_size = max_cache_size

    def generate(self, max_attempts: int = 1000) -> str:
        """Generate a new unique spider-x path.

        Args:
            max_attempts: Maximum number of generation attempts before fallback

        Returns:
            Random path starting with '/' that doesn't collide with
            reserved paths or previously generated paths

        Example:
            >>> gen = SpiderXGenerator()
            >>> path = gen.generate()
            >>> path.startswith('/')
            True
        """
        # Clear cache if it's too large to prevent memory leak
        if len(self._used_paths) > self._max_cache_size:
            logger.warning(f"SpiderX cache size exceeded {self._max_cache_size}, clearing cache")
            self._used_paths.clear()

        # Try to generate unique path with maximum attempts
        for _attempt in range(max_attempts):
            path = self._generate_candidate()

            # Ensure no collision with reserved or used paths
            if path not in RESERVED_PATHS and path not in self._used_paths:
                self._used_paths.add(path)
                return path

        # Fallback: return path without collision check
        logger.warning(
            f"Failed to generate unique path after {max_attempts} attempts, "
            "returning non-unique path"
        )
        return self._generate_candidate()

    def _generate_candidate(self) -> str:
        """Generate a single candidate path.

        Returns:
            Candidate path string
        """
        target_length = random.randint(SPIDERX_MIN_LENGTH, SPIDERX_MAX_LENGTH)

        # Try different token byte lengths
        for byte_count in SPIDERX_CANDIDATES:
            token = secrets.token_urlsafe(byte_count)
            # Clean up base64 characters
            cleaned = token.rstrip("=").replace(".", "_").replace("-", "-")

            if len(cleaned) >= target_length:
                token = cleaned[:target_length]
                break
        else:
            # Fallback if no candidate worked
            token = secrets.token_urlsafe(16).rstrip("=").replace(".", "_")

        return "/" + token.lower()

    def reset(self) -> None:
        """Reset the used paths tracking."""
        self._used_paths.clear()
