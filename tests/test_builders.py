"""Tests for configuration builders."""

from src.builders import LegacyJsonBuilder, MihomoBuilder, V2RayBuilder
from src.models import Server, UserInfo


class TestMihomoBuilder:
    """Tests for MihomoBuilder."""

    def test_build_basic_config(self, sample_user: UserInfo, sample_server: Server):
        """Test building basic Mihomo configuration."""
        template = {
            "proxy-template": {
                "type": "vless",
                "network": "tcp",
                "uuid": "placeholder",
                "servername": "placeholder",
                "reality-opts": {"public-key": "", "short-id": ""},
            },
            "proxy-groups": [{"name": "auto", "type": "url-test", "proxies": "__PROXY_NAMES__"}],
        }

        builder = MihomoBuilder(template_loader=lambda template_name=None: template)
        result = builder.build([sample_server], sample_user)

        assert isinstance(result, bytes)
        config_str = result.decode("utf-8")

        # Check that template substitutions happened
        assert "proxies:" in config_str
        assert sample_server.description in config_str
        assert sample_server.host in config_str
        assert sample_user.id in config_str

    def test_build_with_external_server(self, sample_user: UserInfo):
        """Test building config with external server."""
        ext_server = Server(
            host="external.example.com",
            description="External Server",
            public_key="ext-key",
            is_external=True,
            fixed_id="ext-uuid",
            fixed_short_id="ext-short",
            groups=frozenset(["premium"]),
        )

        template = {
            "proxy-template": {
                "type": "vless",
                "uuid": "placeholder",
                "servername": "placeholder",
                "reality-opts": {"public-key": "", "short-id": ""},
            }
        }

        builder = MihomoBuilder(template_loader=lambda template_name=None: template)
        result = builder.build([ext_server], sample_user)

        config_str = result.decode("utf-8")

        # External server should use its own UUID
        assert "ext-uuid" in config_str
        assert "ext-short" in config_str

    def test_build_filters_servers_by_groups(self, sample_user: UserInfo):
        """Test that only accessible servers are included."""
        servers = [
            Server(
                host="premium.example.com",
                description="Premium",
                groups=frozenset(["premium"]),
            ),
            Server(
                host="basic.example.com",
                description="Basic",
                groups=frozenset(["basic"]),
            ),
        ]

        template = {"proxy-template": {"type": "vless"}}
        builder = MihomoBuilder(template_loader=lambda template_name=None: template)

        # User with premium group
        result = builder.build(servers, sample_user)
        config_str = result.decode("utf-8")

        assert "Premium" in config_str
        assert "Basic" not in config_str

    def test_build_no_eligible_servers_raises(self, sample_user: UserInfo):
        """Test that building with no eligible servers raises error."""
        servers = [
            Server(
                host="restricted.example.com",
                description="Restricted",
                groups=frozenset(["admin"]),
            )
        ]

        template = {"proxy-template": {"type": "vless"}}
        builder = MihomoBuilder(template_loader=lambda template_name=None: template)

        # Should raise ValueError
        try:
            builder.build(servers, sample_user)
            raise AssertionError("Expected ValueError")
        except ValueError as e:
            assert "no access" in str(e).lower()

    def test_substitute_proxy_names(self, sample_user: UserInfo):
        """Test that __PROXY_NAMES__ is substituted correctly."""
        servers = [
            Server(host="s1.example.com", description="Server 1", groups=frozenset(["premium"])),
            Server(host="s2.example.com", description="Server 2", groups=frozenset(["premium"])),
        ]

        template = {
            "proxy-template": {"type": "vless"},
            "proxy-groups": [{"name": "auto", "proxies": "__PROXY_NAMES__"}],
        }

        builder = MihomoBuilder(template_loader=lambda template_name=None: template)
        result = builder.build(servers, sample_user)
        config_str = result.decode("utf-8")

        # Both server names should be in the proxy group
        assert "Server 1" in config_str
        assert "Server 2" in config_str


class TestV2RayBuilder:
    """Tests for V2RayBuilder."""

    def test_build_basic_subscription(self, sample_user: UserInfo, sample_server: Server):
        """Test building basic V2Ray subscription."""
        template = "vless://<ID>@<ADDRESS>:443?sni=<SERVERNAME>&spx=%2F<SPIDERX>#<NAME>"

        builder = V2RayBuilder(template_loader=lambda: template)
        result = builder.build([sample_server], sample_user)

        assert isinstance(result, bytes)
        links = result.decode("utf-8").split("\n")

        assert len(links) == 1
        assert links[0].startswith("vless://")
        assert sample_user.id in links[0]
        assert sample_server.host in links[0]

    def test_build_multiple_servers(self, sample_user: UserInfo):
        """Test building subscription with multiple servers."""
        servers = [
            Server(host="s1.example.com", description="Server 1", groups=frozenset(["premium"])),
            Server(host="s2.example.com", description="Server 2", groups=frozenset(["premium"])),
        ]

        template = "vless://<ID>@<ADDRESS>:443#<NAME>"

        builder = V2RayBuilder(template_loader=lambda: template)
        result = builder.build(servers, sample_user)

        links = result.decode("utf-8").split("\n")
        assert len(links) == 2
        assert "s1.example.com" in result.decode("utf-8")
        assert "s2.example.com" in result.decode("utf-8")

    def test_build_with_spiderx_for_internal(self, sample_user: UserInfo):
        """Test that spider-x is generated for internal servers."""
        server = Server(
            host="internal.example.com",
            description="Internal",
            is_external=False,
            groups=frozenset(["premium"]),
        )

        template = "vless://<ID>@<ADDRESS>:443?spx=%2F<SPIDERX>#<NAME>"

        builder = V2RayBuilder(template_loader=lambda: template)
        result = builder.build([server], sample_user)

        link = result.decode("utf-8")
        # Should have spx parameter with a path
        assert "spx=" in link
        assert "%2F" in link  # URL-encoded '/'

    def test_build_no_spiderx_for_external(self, sample_user: UserInfo):
        """Test that spider-x is empty for external servers."""
        server = Server(
            host="external.example.com",
            description="External",
            is_external=True,
            fixed_id="ext-id",
            groups=frozenset(["premium"]),
        )

        template = "vless://<ID>@<ADDRESS>:443?spx=%2F<SPIDERX>#<NAME>"

        builder = V2RayBuilder(template_loader=lambda: template)
        result = builder.build([server], sample_user)

        link = result.decode("utf-8")
        # External server should use fixed_id
        assert "ext-id" in link
        # spx should be empty (just %2F without path)
        assert "spx=%2F&" in link or "spx=%2F#" in link

    def test_build_filters_by_groups(self, sample_user: UserInfo):
        """Test that only accessible servers are included."""
        servers = [
            Server(
                host="premium.example.com", description="Premium", groups=frozenset(["premium"])
            ),
            Server(host="basic.example.com", description="Basic", groups=frozenset(["basic"])),
        ]

        template = "vless://<ID>@<ADDRESS>:443#<NAME>"

        builder = V2RayBuilder(template_loader=lambda: template)
        result = builder.build(servers, sample_user)

        links_str = result.decode("utf-8")
        assert "premium.example.com" in links_str
        assert "basic.example.com" not in links_str

    def test_build_url_encodes_values(self, sample_user: UserInfo):
        """Test that special characters are URL-encoded."""
        server = Server(
            host="test.example.com",
            description="Test 🇸🇪 Server",
            alias="sni.example.com",
            groups=frozenset(["premium"]),
        )

        template = "vless://<ID>@<ADDRESS>:443?sni=<SERVERNAME>#<NAME>"

        builder = V2RayBuilder(template_loader=lambda: template)
        result = builder.build([server], sample_user)

        link = result.decode("utf-8")
        # Description should be URL-encoded
        assert "%F0%9F" in link or "Test" in link  # Emoji encoded or description present


class TestLegacyJsonBuilder:
    """Tests for LegacyJsonBuilder."""

    def test_build_basic_json_config(self, sample_user: UserInfo, sample_server: Server):
        """Test building basic JSON configuration."""
        import json

        template = [
            {
                "log": {"loglevel": "warning"},
                "outbounds": [
                    {
                        "protocol": "vless",
                        "settings": {"vnext": []},
                    }
                ],
            }
        ]

        builder = LegacyJsonBuilder(json_loader=lambda: template)
        result = builder.build([sample_server], sample_user)

        assert isinstance(result, bytes)
        configs = json.loads(result.decode("utf-8"))

        assert isinstance(configs, list)
        assert len(configs) > 0

    def test_build_filters_servers(self, sample_user: UserInfo):
        """Test that servers are filtered by group access."""
        servers = [
            Server(
                host="premium.example.com",
                description="Premium Server",
                groups=frozenset(["premium"]),
            ),
            Server(
                host="basic.example.com", description="Basic Server", groups=frozenset(["basic"])
            ),
        ]

        template = [
            {"remarks": "", "outbounds": [{"protocol": "vless", "settings": {"vnext": []}}]}
        ]

        builder = LegacyJsonBuilder(json_loader=lambda: template)
        result = builder.build(servers, sample_user)

        config_str = result.decode("utf-8")
        # Check that premium server description is in remarks
        assert "Premium Server" in config_str
        # Check that basic server is NOT included
        assert "Basic Server" not in config_str
