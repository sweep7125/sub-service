"""Tests for service layer."""

from pathlib import Path

from src.models import AppConfig
from src.services import ConfigService


class TestConfigService:
    """Tests for ConfigService."""

    def test_initialization(self, app_config: AppConfig):
        """Test service initialization."""
        service = ConfigService(app_config)

        assert service.config == app_config
        assert service.repos is not None
        assert service.mihomo_builder is not None
        assert service.v2ray_builder is not None
        assert service.legacy_builder is not None

    def test_get_servers(self, app_config: AppConfig):
        """Test getting all servers."""
        service = ConfigService(app_config)
        servers = service.get_servers()

        assert len(servers) == 4
        assert all(hasattr(s, "host") for s in servers)

    def test_find_user(self, app_config: AppConfig):
        """Test finding user by prefix."""
        service = ConfigService(app_config)

        user = service.find_user("user1")
        assert user is not None
        assert user.link_path == "user1"

        user = service.find_user("user1/config/mihomo")
        assert user is not None
        assert user.link_path == "user1"

    def test_find_user_not_found(self, app_config: AppConfig):
        """Test finding non-existent user."""
        service = ConfigService(app_config)

        user = service.find_user("nonexistent")
        assert user is None

    def test_build_mihomo_config(self, app_config: AppConfig):
        """Test building Mihomo configuration."""
        service = ConfigService(app_config)
        servers = service.get_servers()
        user = service.find_user("user1")

        assert user is not None

        # Filter servers for user
        eligible = [s for s in servers if not s.groups or user.has_access_to_groups(s.groups)]

        result = service.build_mihomo_config(eligible, user)

        assert isinstance(result, bytes)
        assert len(result) > 0

        config_str = result.decode("utf-8")
        assert "proxies:" in config_str

    def test_build_v2ray_config(self, app_config: AppConfig):
        """Test building V2Ray subscription."""
        service = ConfigService(app_config)
        servers = service.get_servers()
        user = service.find_user("user1")

        assert user is not None

        # Filter servers for user
        eligible = [s for s in servers if not s.groups or user.has_access_to_groups(s.groups)]

        result = service.build_v2ray_config(eligible, user)

        assert isinstance(result, bytes)
        assert len(result) > 0

        links = result.decode("utf-8")
        assert "vless://" in links

    def test_build_legacy_config(self, app_config: AppConfig):
        """Test building legacy JSON configuration."""
        service = ConfigService(app_config)
        servers = service.get_servers()
        user = service.find_user("user1")

        assert user is not None

        # Filter servers for user
        eligible = [s for s in servers if not s.groups or user.has_access_to_groups(s.groups)]

        result = service.build_legacy_config(eligible, user)

        assert isinstance(result, bytes)
        assert len(result) > 0


class TestServerFilterService:
    """Tests for server filtering functions."""

    def test_filter_by_user_groups(self, multiple_servers):
        """Test filtering servers by user groups."""
        from src.models import UserInfo
        from src.services.server_filter_service import filter_servers_by_groups

        user = UserInfo(id="test-id", groups=frozenset(["premium"]))

        filtered = filter_servers_by_groups(multiple_servers, user)

        # Should include premium servers and servers without groups
        assert len(filtered) >= 1
        assert all(not s.groups or user.has_access_to_groups(s.groups) for s in filtered)

    def test_filter_includes_public_servers(self, multiple_servers):
        """Test that public servers (no groups) are included."""
        from src.models import Server, UserInfo
        from src.services.server_filter_service import filter_servers_by_groups

        public_server = Server(
            host="public.example.com",
            description="Public Server",
            groups=frozenset(),
        )
        servers = [*multiple_servers, public_server]

        user = UserInfo(id="test-id", groups=frozenset(["premium"]))

        filtered = filter_servers_by_groups(servers, user)

        # Public server should always be included
        assert any(s.host == "public.example.com" for s in filtered)

    def test_filter_empty_user_groups(self, multiple_servers):
        """Test filtering when user has no groups."""
        from src.models import UserInfo
        from src.services.server_filter_service import filter_servers_by_groups

        user = UserInfo(id="test-id", groups=frozenset())

        filtered = filter_servers_by_groups(multiple_servers, user)

        # Should only include servers without groups
        assert all(not s.groups for s in filtered)

    def test_filter_no_matching_servers(self, multiple_servers):
        """Test filtering when no servers match user groups."""
        from src.models import UserInfo
        from src.services.server_filter_service import filter_servers_by_groups

        user = UserInfo(id="test-id", groups=frozenset(["nonexistent"]))

        # Remove servers without groups
        servers_with_groups = [s for s in multiple_servers if s.groups]

        filtered = filter_servers_by_groups(servers_with_groups, user)

        assert len(filtered) == 0


class TestGeoFileService:
    """Tests for GeoFileService."""

    def test_initialization(self, temp_dir: Path):
        """Test GeoFileService initialization."""
        from src.services import GeoFileService

        service = GeoFileService(cache_dir=temp_dir, cache_ttl=600)

        assert service.cache_dir == temp_dir
        assert service.cache_ttl == 600

    def test_get_last_updated_timestamp(self, temp_dir: Path):
        """Test getting last updated timestamp."""
        from src.services import GeoFileService

        service = GeoFileService(cache_dir=temp_dir, cache_ttl=600)
        timestamp = service.get_last_updated_timestamp()

        # Should return a timestamp (int)
        assert isinstance(timestamp, int)
        assert timestamp >= 0

    def test_build_routing_header(self, temp_dir: Path):
        """Test building routing header."""
        from src.services import GeoFileService

        service = GeoFileService(cache_dir=temp_dir, cache_ttl=600)
        template = {"dns": "https://dns.google/dns-query", "rules": []}

        header = service.build_routing_header(template)

        # Should return base64-encoded header
        assert isinstance(header, str)
        assert header.startswith("happ://routing/onadd/") or header == ""
