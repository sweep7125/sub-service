"""Tests for utility functions."""

from src.constants import RESERVED_PATHS
from src.utils import SpiderXGenerator


class TestSpiderXGenerator:
    """Tests for SpiderXGenerator."""

    def test_generate_returns_path(self, spiderx_generator: SpiderXGenerator):
        """Test that generate returns a path starting with /."""
        path = spiderx_generator.generate()

        assert path.startswith("/")
        assert len(path) > 1

    def test_generate_unique_paths(self, spiderx_generator: SpiderXGenerator):
        """Test that generator creates unique paths."""
        paths = {spiderx_generator.generate() for _ in range(100)}

        # Should have at least 95 unique paths out of 100
        assert len(paths) >= 95

    def test_generate_avoids_reserved_paths(self, spiderx_generator: SpiderXGenerator):
        """Test that generated paths don't collide with reserved paths."""
        for _ in range(100):
            path = spiderx_generator.generate()
            assert path not in RESERVED_PATHS

    def test_generate_within_length_bounds(self, spiderx_generator: SpiderXGenerator):
        """Test that generated paths are within expected length."""
        for _ in range(50):
            path = spiderx_generator.generate()
            # Path includes leading '/', so actual content is len(path) - 1
            assert 8 <= len(path) <= 33  # Min 8, max 32 + '/'

    def test_reset_clears_cache(self, spiderx_generator: SpiderXGenerator):
        """Test that reset clears the used paths cache."""
        # Generate some paths
        for _ in range(10):
            spiderx_generator.generate()

        # Reset should clear internal cache
        spiderx_generator.reset()

        # After reset, should still generate valid paths
        path = spiderx_generator.generate()
        assert path.startswith("/")

    def test_path_format(self, spiderx_generator: SpiderXGenerator):
        """Test that paths contain only valid URL-safe characters."""
        for _ in range(20):
            path = spiderx_generator.generate()
            # Remove leading '/'
            content = path[1:]

            # Should be URL-safe (alphanumeric, dash, underscore)
            assert content.replace("-", "").replace("_", "").isalnum()

    def test_max_cache_size_clearing(self):
        """Test that cache is cleared when it exceeds max size."""
        generator = SpiderXGenerator(max_cache_size=10)

        # Generate more than max_cache_size paths
        for _ in range(15):
            generator.generate()

        # Should still work without errors
        path = generator.generate()
        assert path.startswith("/")

    def test_fallback_on_collision_attempts(self):
        """Test fallback behavior when max attempts exceeded."""
        # Create generator with small cache
        generator = SpiderXGenerator(max_cache_size=5)

        # Generate with low max_attempts to test fallback
        path = generator.generate(max_attempts=1)
        assert path.startswith("/")


class TestTextUtils:
    """Tests for text utility functions."""

    def test_decode_unicode_escapes(self):
        """Test decoding unicode escape sequences."""
        from src.utils import decode_unicode_escapes

        # Test flag emojis
        text = r"\U0001F1F8\U0001F1EA Sweden"
        result = decode_unicode_escapes(text)
        assert "🇸🇪" in result
        assert "Sweden" in result

    def test_decode_unicode_escapes_no_escapes(self):
        """Test text without escape sequences."""
        from src.utils import decode_unicode_escapes

        text = "Plain text"
        result = decode_unicode_escapes(text)
        assert result == "Plain text"

    def test_decode_unicode_escapes_empty(self):
        """Test empty string."""
        from src.utils import decode_unicode_escapes

        result = decode_unicode_escapes("")
        assert result == ""

    def test_decode_unicode_escapes_mixed(self):
        """Test mixed text with and without escapes."""
        from src.utils import decode_unicode_escapes

        text = r"Server \U0001F1FA\U0001F1F8 USA-01"
        result = decode_unicode_escapes(text)
        assert "🇺🇸" in result
        assert "USA-01" in result


class TestCacheUtils:
    """Tests for cache utilities."""

    def test_file_cache_basic(self, temp_dir):
        """Test basic file caching."""
        from pathlib import Path

        from src.utils import FileCache

        cache = FileCache()
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content", encoding="utf-8")

        def loader(path: Path) -> str:
            return path.read_text(encoding="utf-8")

        # First call should load from file
        result1 = cache.get(test_file, loader)
        assert result1 == "test content"

        # Second call should use cache
        result2 = cache.get(test_file, loader)
        assert result2 == "test content"

    def test_file_cache_invalidation(self, temp_dir):
        """Test cache invalidation on file modification."""
        import time
        from pathlib import Path

        from src.utils import FileCache

        cache = FileCache()
        test_file = temp_dir / "test.txt"
        test_file.write_text("original", encoding="utf-8")

        def loader(path: Path) -> str:
            return path.read_text(encoding="utf-8")

        # First call
        result1 = cache.get(test_file, loader)
        assert result1 == "original"

        # Modify file
        time.sleep(0.01)  # Ensure mtime changes
        test_file.write_text("modified", encoding="utf-8")

        # Should reload from file
        result2 = cache.get(test_file, loader)
        assert result2 == "modified"

    def test_file_cache_missing_file(self, temp_dir):
        """Test cache with missing file."""
        from pathlib import Path

        from src.utils import FileCache

        cache = FileCache()
        nonexistent = temp_dir / "nonexistent.txt"

        def loader(path: Path) -> str:
            return path.read_text(encoding="utf-8")

        result = cache.get(nonexistent, loader)
        assert result is None


class TestNetworkUtils:
    """Tests for network utility functions."""

    def test_get_client_ip_from_x_forwarded_for(self):
        """Test extracting IP from X-Forwarded-For header."""
        from unittest.mock import Mock

        from src.utils import get_client_ip

        request = Mock()
        request.headers.get.return_value = "203.0.113.1, 198.51.100.1"
        request.remote_addr = "192.168.1.1"

        ip = get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_from_x_real_ip(self):
        """Test extracting IP from X-Real-IP header."""
        from unittest.mock import Mock

        from src.utils import get_client_ip

        request = Mock()
        request.headers.get.side_effect = lambda h: (
            "203.0.113.1" if h == "X-Real-IP" else None
        )
        request.remote_addr = "192.168.1.1"

        ip = get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_fallback_to_remote_addr(self):
        """Test fallback to remote_addr when no proxy headers."""
        from unittest.mock import Mock

        from src.utils import get_client_ip

        request = Mock()
        request.headers.get.return_value = None
        request.remote_addr = "203.0.113.1"

        ip = get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_default_unknown(self):
        """Test default 'unknown' when no IP available."""
        from unittest.mock import Mock

        from src.utils import get_client_ip

        request = Mock()
        request.headers.get.return_value = None
        request.remote_addr = None

        ip = get_client_ip(request)
        assert ip == "unknown"
