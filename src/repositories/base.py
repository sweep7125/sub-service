"""Base repository interface."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TypeVar

from ..utils import FileCache

T = TypeVar("T")


class BaseRepository[T](ABC):
    """Base class for all repositories.

    Provides caching functionality and defines the repository interface.
    """

    def __init__(self, file_path: Path) -> None:
        """Initialize repository with file path.

        Args:
            file_path: Path to the data file
        """
        self.file_path = file_path
        self._cache = FileCache[T]()

    @abstractmethod
    def _load_from_file(self, path: Path) -> T:
        """Load data from file.

        Args:
            path: File path to load from

        Returns:
            Loaded data
        """
        pass

    def get(self) -> T:
        """Get data with caching.

        Returns:
            Cached or freshly loaded data
        """
        result = self._cache.get(self.file_path, self._load_from_file)
        return result if result is not None else self._get_default()

    @abstractmethod
    def _get_default(self) -> T:
        """Get default value when file doesn't exist.

        Returns:
            Default value
        """
        pass

    def invalidate_cache(self) -> None:
        """Invalidate cached data."""
        self._cache.invalidate(self.file_path)
