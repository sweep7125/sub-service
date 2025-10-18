"""File-based caching utilities."""

import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


class FileCache[T]:
    """Thread-safe file cache based on modification time and size.

    Caches file contents based on (mtime_ns, size) tuple to avoid
    unnecessary file reads when content hasn't changed.

    Thread-safe implementation using RLock to prevent race conditions
    in concurrent access scenarios.
    """

    def __init__(self) -> None:
        """Initialize empty cache with thread lock."""
        self._cache: dict[Path, dict[str, Any]] = {}
        self._lock = threading.RLock()

    def _get_cache_key(self, path: Path) -> tuple[int, int] | None:
        """Get cache key from file stats.

        Args:
            path: File path to check

        Returns:
            Tuple of (mtime_ns, size) or None if file doesn't exist
        """
        try:
            stat = path.stat()
            return (stat.st_mtime_ns, stat.st_size)
        except FileNotFoundError:
            return None

    def get(self, path: Path, loader: Callable[[Path], T]) -> T | None:
        """Get cached content or load from file (thread-safe).

        Args:
            path: File path to read
            loader: Function to load file content if not cached

        Returns:
            Cached or loaded content, or None if file doesn't exist
        """
        cache_key = self._get_cache_key(path)
        if cache_key is None:
            return None

        with self._lock:
            # Check if we have valid cached data
            entry = self._cache.get(path)
            if entry and entry.get("key") == cache_key:
                return entry["data"]

            # Load and cache new data
            data = loader(path)
            self._cache[path] = {"key": cache_key, "data": data}
            return data

    def invalidate(self, path: Path) -> None:
        """Invalidate cache entry for a specific path (thread-safe).

        Args:
            path: Path to invalidate
        """
        with self._lock:
            self._cache.pop(path, None)

    def clear(self) -> None:
        """Clear all cache entries (thread-safe)."""
        with self._lock:
            self._cache.clear()
