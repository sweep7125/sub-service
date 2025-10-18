"""Tests for repository layer."""

from pathlib import Path

from src.repositories import ServerRepository, UserRepository


class TestUserRepository:
    """Tests for UserRepository."""

    def test_load_users_from_file(self, sample_users_file: Path):
        """Test loading users from configuration file."""
        repo = UserRepository(sample_users_file)
        users = repo.get()

        assert len(users) == 4
        assert "user1" in users
        assert "user2" in users
        assert "user3" in users
        assert "user4" in users

    def test_user_parsing(self, sample_users_file: Path):
        """Test correct parsing of user attributes."""
        repo = UserRepository(sample_users_file)
        users = repo.get()

        user1 = users["user1"]
        assert user1.id == "550e8400-e29b-41d4-a716-446655440001"
        assert user1.short_id == "aabbccdd"
        assert user1.link_path == "user1"
        assert user1.comment == "Test User 1"
        assert user1.groups == frozenset(["premium", "vip"])

    def test_user_without_short_id(self, sample_users_file: Path):
        """Test user without short ID."""
        repo = UserRepository(sample_users_file)
        users = repo.get()

        user4 = users["user4"]
        assert user4.short_id is None
        assert user4.get_short_id() == ""

    def test_user_with_empty_groups(self, sample_users_file: Path):
        """Test user with empty groups gets default group."""
        repo = UserRepository(sample_users_file)
        users = repo.get()

        user3 = users["user3"]
        assert user3.groups == frozenset(["default"])

    def test_find_by_prefix_exact_match(self, sample_users_file: Path):
        """Test finding user by exact prefix match."""
        repo = UserRepository(sample_users_file)

        user = repo.find_by_prefix("user1")
        assert user is not None
        assert user.link_path == "user1"

    def test_find_by_prefix_with_suffix(self, sample_users_file: Path):
        """Test finding user when prefix has additional path."""
        repo = UserRepository(sample_users_file)

        user = repo.find_by_prefix("user1/config/mihomo")
        assert user is not None
        assert user.link_path == "user1"

    def test_find_by_prefix_longest_match(self, temp_dir: Path):
        """Test that longest matching prefix is returned."""
        users_file = temp_dir / "users"
        users_file.write_text(
            "550e8400-e29b-41d4-a716-446655440001||user|User 1|\n"
            "550e8400-e29b-41d4-a716-446655440002||user/sub|User 2|\n",
            encoding="utf-8",
        )

        repo = UserRepository(users_file)
        user = repo.find_by_prefix("user/sub/path")

        assert user is not None
        assert user.link_path == "user/sub"

    def test_find_by_prefix_not_found(self, sample_users_file: Path):
        """Test finding non-existent user."""
        repo = UserRepository(sample_users_file)

        user = repo.find_by_prefix("nonexistent")
        assert user is None

    def test_find_by_prefix_empty(self, sample_users_file: Path):
        """Test finding with empty prefix."""
        repo = UserRepository(sample_users_file)

        user = repo.find_by_prefix("")
        assert user is None

    def test_invalid_uuid_skipped(self, temp_dir: Path):
        """Test that lines with invalid UUID are skipped."""
        users_file = temp_dir / "users"
        users_file.write_text(
            "invalid-uuid|shortid|user1|User 1|premium\n"
            "550e8400-e29b-41d4-a716-446655440001|shortid|user2|User 2|premium\n",
            encoding="utf-8",
        )

        repo = UserRepository(users_file)
        users = repo.get()

        assert len(users) == 1
        assert "user2" in users
        assert "user1" not in users

    def test_empty_file(self, temp_dir: Path):
        """Test loading from empty file."""
        users_file = temp_dir / "users"
        users_file.write_text("", encoding="utf-8")

        repo = UserRepository(users_file)
        users = repo.get()

        assert len(users) == 0

    def test_comments_and_empty_lines_ignored(self, temp_dir: Path):
        """Test that comments and empty lines are ignored."""
        users_file = temp_dir / "users"
        users_file.write_text(
            "# Comment line\n"
            "\n"
            "550e8400-e29b-41d4-a716-446655440001|shortid|user1|User 1|premium\n"
            "   # Another comment\n"
            "\n"
            "550e8400-e29b-41d4-a716-446655440002|shortid|user2|User 2|premium\n",
            encoding="utf-8",
        )

        repo = UserRepository(users_file)
        users = repo.get()

        assert len(users) == 2

    def test_missing_file_returns_empty(self, temp_dir: Path):
        """Test that missing file returns empty dict."""
        nonexistent = temp_dir / "nonexistent"
        repo = UserRepository(nonexistent)
        users = repo.get()

        assert len(users) == 0


class TestServerRepository:
    """Tests for ServerRepository."""

    def test_load_servers_from_file(self, sample_servers_file: Path):
        """Test loading servers from configuration file."""
        repo = ServerRepository(sample_servers_file)
        servers = repo.get()

        assert len(servers) == 4

    def test_server_parsing(self, sample_servers_file: Path):
        """Test correct parsing of server attributes."""
        repo = ServerRepository(sample_servers_file)
        servers = repo.get()

        server1 = servers[0]
        assert server1.host == "server1.example.com"
        assert server1.alias == "sni1.example.com"
        assert server1.dns_override == "https://dns.google/dns-query"
        assert server1.public_key == "pubkey1"
        assert server1.description == "Server 1"
        assert server1.groups == frozenset(["premium", "vip"])
        assert server1.is_external is False

    def test_external_server(self, sample_servers_file: Path):
        """Test external server parsing."""
        repo = ServerRepository(sample_servers_file)
        servers = repo.get()

        ext_server = servers[3]
        assert ext_server.host == "external.example.com"
        assert ext_server.is_external is True
        assert ext_server.fixed_id == "ext-uuid"
        assert ext_server.fixed_short_id == "ext-short"
        assert ext_server.groups == frozenset(["premium"])

    def test_server_without_groups(self, sample_servers_file: Path):
        """Test server with empty groups."""
        repo = ServerRepository(sample_servers_file)
        servers = repo.get()

        server3 = servers[2]
        assert server3.groups == frozenset()

    def test_server_name_fallback(self, sample_servers_file: Path):
        """Test that server_name uses alias or host."""
        repo = ServerRepository(sample_servers_file)
        servers = repo.get()

        assert servers[0].server_name == "sni1.example.com"
        assert servers[2].server_name == "server3.example.com"  # No alias

    def test_unicode_escapes_decoded(self, temp_dir: Path):
        """Test that unicode escapes in description are decoded."""
        servers_file = temp_dir / "servers"
        servers_file.write_text(
            r"server.example.com|sni||key|\U0001F1F8\U0001F1EA Sweden|premium|internal||" + "\n",
            encoding="utf-8",
        )

        repo = ServerRepository(servers_file)
        servers = repo.get()

        assert len(servers) == 1
        assert "🇸🇪" in servers[0].description

    def test_empty_file(self, temp_dir: Path):
        """Test loading from empty file."""
        servers_file = temp_dir / "servers"
        servers_file.write_text("", encoding="utf-8")

        repo = ServerRepository(servers_file)
        servers = repo.get()

        assert len(servers) == 0

    def test_comments_ignored(self, temp_dir: Path):
        """Test that comments and empty lines are ignored."""
        servers_file = temp_dir / "servers"
        servers_file.write_text(
            "# Comment\n"
            "\n"
            "server1.example.com|sni||key|Server 1|premium|internal||\n"
            "# Another comment\n"
            "server2.example.com|sni||key|Server 2|premium|internal||\n",
            encoding="utf-8",
        )

        repo = ServerRepository(servers_file)
        servers = repo.get()

        assert len(servers) == 2

    def test_missing_required_fields_skipped(self, temp_dir: Path):
        """Test that lines with missing required fields are skipped."""
        servers_file = temp_dir / "servers"
        servers_file.write_text(
            "|||\n"  # Missing host
            "server1.example.com|sni||key|Server 1|premium|internal||\n",
            encoding="utf-8",
        )

        repo = ServerRepository(servers_file)
        servers = repo.get()

        assert len(servers) == 1

    def test_missing_file_returns_empty(self, temp_dir: Path):
        """Test that missing file returns empty list."""
        nonexistent = temp_dir / "nonexistent"
        repo = ServerRepository(nonexistent)
        servers = repo.get()

        assert len(servers) == 0

    def test_default_internal_type(self, temp_dir: Path):
        """Test that servers default to internal type."""
        servers_file = temp_dir / "servers"
        servers_file.write_text(
            "server.example.com|sni||key|Server|premium|||\n",
            encoding="utf-8",
        )

        repo = ServerRepository(servers_file)
        servers = repo.get()

        assert len(servers) == 1
        assert servers[0].is_external is False
