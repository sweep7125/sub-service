"""Tests for User and Server models."""

import pytest

from src.models import Server, UserInfo


class TestUserInfo:
    """Tests for UserInfo model."""

    def test_user_creation(self):
        """Test creating a UserInfo instance."""
        user = UserInfo(
            id="550e8400-e29b-41d4-a716-446655440000",
            short_id="12345678",
            spider_x="/test-path",
            comment="Test User",
            link_path="testuser",
            groups=frozenset(["premium", "vip"]),
        )

        assert user.id == "550e8400-e29b-41d4-a716-446655440000"
        assert user.short_id == "12345678"
        assert user.spider_x == "/test-path"
        assert user.comment == "Test User"
        assert user.link_path == "testuser"
        assert user.groups == frozenset(["premium", "vip"])

    def test_user_with_defaults(self):
        """Test UserInfo with default values."""
        user = UserInfo(id="550e8400-e29b-41d4-a716-446655440000")

        assert user.id == "550e8400-e29b-41d4-a716-446655440000"
        assert user.short_id is None
        assert user.spider_x is None
        assert user.comment == ""
        assert user.link_path == ""
        assert user.groups == frozenset()

    def test_get_short_id_with_value(self):
        """Test get_short_id when short_id is set."""
        user = UserInfo(id="test-id", short_id="12345678")
        assert user.get_short_id() == "12345678"
        assert user.get_short_id("default") == "12345678"

    def test_get_short_id_with_none(self):
        """Test get_short_id when short_id is None."""
        user = UserInfo(id="test-id", short_id=None)
        assert user.get_short_id() == ""
        assert user.get_short_id("default") == "default"

    def test_is_in_group(self):
        """Test checking if user is in a group."""
        user = UserInfo(id="test-id", groups=frozenset(["premium", "vip"]))

        assert user.is_in_group("premium") is True
        assert user.is_in_group("vip") is True
        assert user.is_in_group("default") is False
        assert user.is_in_group("nonexistent") is False

    def test_has_access_to_groups_with_intersection(self):
        """Test access when user and server share groups."""
        user = UserInfo(id="test-id", groups=frozenset(["premium", "vip"]))
        server_groups = frozenset(["premium", "basic"])

        assert user.has_access_to_groups(server_groups) is True

    def test_has_access_to_groups_no_intersection(self):
        """Test access when user and server have no common groups."""
        user = UserInfo(id="test-id", groups=frozenset(["premium"]))
        server_groups = frozenset(["basic", "default"])

        assert user.has_access_to_groups(server_groups) is False

    def test_has_access_to_empty_server_groups(self):
        """Test access when server has no groups (public server)."""
        user = UserInfo(id="test-id", groups=frozenset(["premium"]))
        server_groups = frozenset()

        assert user.has_access_to_groups(server_groups) is True

    def test_has_access_with_empty_user_groups(self):
        """Test access when user has no groups but server does."""
        user = UserInfo(id="test-id", groups=frozenset())
        server_groups = frozenset(["premium"])

        assert user.has_access_to_groups(server_groups) is False

    def test_user_immutability(self):
        """Test that UserInfo is immutable (frozen dataclass)."""
        user = UserInfo(id="test-id", short_id="12345678")

        with pytest.raises(AttributeError):
            user.short_id = "new-id"  # type: ignore


class TestServer:
    """Tests for Server model."""

    def test_server_creation(self):
        """Test creating a Server instance."""
        server = Server(
            host="test.example.com",
            description="Test Server",
            alias="alias.example.com",
            dns_override="https://dns.google/dns-query",
            public_key="test-public-key",
            fixed_id="fixed-uuid",
            fixed_short_id="fixed-short",
            is_external=True,
            groups=frozenset(["premium", "vip"]),
        )

        assert server.host == "test.example.com"
        assert server.description == "Test Server"
        assert server.alias == "alias.example.com"
        assert server.dns_override == "https://dns.google/dns-query"
        assert server.public_key == "test-public-key"
        assert server.fixed_id == "fixed-uuid"
        assert server.fixed_short_id == "fixed-short"
        assert server.is_external is True
        assert server.groups == frozenset(["premium", "vip"])

    def test_server_with_defaults(self):
        """Test Server with default values."""
        server = Server(host="test.example.com", description="Test Server")

        assert server.host == "test.example.com"
        assert server.description == "Test Server"
        assert server.alias is None
        assert server.dns_override is None
        assert server.public_key is None
        assert server.fixed_id is None
        assert server.fixed_short_id is None
        assert server.is_external is False
        assert server.groups == frozenset()

    def test_is_in_group(self):
        """Test checking if server is in a group."""
        server = Server(
            host="test.example.com",
            description="Test",
            groups=frozenset(["premium", "vip"]),
        )

        assert server.is_in_group("premium") is True
        assert server.is_in_group("vip") is True
        assert server.is_in_group("default") is False

    def test_server_name_with_alias(self):
        """Test server_name property when alias is set."""
        server = Server(
            host="test.example.com",
            description="Test",
            alias="alias.example.com",
        )

        assert server.server_name == "alias.example.com"

    def test_server_name_without_alias(self):
        """Test server_name property when alias is None."""
        server = Server(host="test.example.com", description="Test", alias=None)

        assert server.server_name == "test.example.com"

    def test_server_immutability(self):
        """Test that Server is immutable (frozen dataclass)."""
        server = Server(host="test.example.com", description="Test")

        with pytest.raises(AttributeError):
            server.host = "new-host.example.com"  # type: ignore

    def test_external_server(self):
        """Test external server configuration."""
        server = Server(
            host="external.example.com",
            description="External Server",
            is_external=True,
            fixed_id="ext-uuid",
            fixed_short_id="ext-short",
        )

        assert server.is_external is True
        assert server.fixed_id == "ext-uuid"
        assert server.fixed_short_id == "ext-short"

    def test_internal_server(self):
        """Test internal server configuration."""
        server = Server(
            host="internal.example.com",
            description="Internal Server",
            is_external=False,
        )

        assert server.is_external is False
        assert server.fixed_id is None
        assert server.fixed_short_id is None
