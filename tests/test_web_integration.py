"""Integration tests for web application."""

from unittest.mock import patch

from src.models import AppConfig
from src.web import _is_allowed_subscription_user_agent, create_app

ALLOWED_BROWSER_UA = "Mozilla/5.0 Chrome/124.0.0.0"


class TestWebApplication:
    """Tests for Flask web application."""

    def test_app_creation(self, app_config: AppConfig):
        """Test that app can be created."""
        app = create_app(app_config)

        assert app is not None
        assert app.config is not None

    def test_security_blocks_insecure_connections(self, app_config: AppConfig):
        """Test that insecure connections are blocked."""
        app = create_app(app_config)
        client = app.test_client()

        # Mock request without secure headers
        with patch("src.web._is_secure_connection", return_value=False):
            response = client.get("/secret/user1")
            # App redirects to "/" on errors, returns 302
            assert response.status_code == 302

    def test_localhost_connection_allowed(self, app_config: AppConfig):
        """Test that localhost connections are allowed."""
        app = create_app(app_config)
        client = app.test_client()

        # Test with localhost (mocked as secure)
        with patch("src.web._is_secure_connection", return_value=True):
            # User path that doesn't exist will 404, but should pass security
            response = client.get("/secret/nonexistent")
            # Should not be 403 (Forbidden), but likely 404 (Not Found)
            assert response.status_code != 403

    def test_request_with_user_path(self, app_config: AppConfig):
        """Test request with valid user path."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get("/secret/user1", headers={"User-Agent": ALLOWED_BROWSER_UA})

            assert response.status_code == 200
            assert response.mimetype == "application/json"
            assert response.data.startswith(b"[")

    def test_mihomo_config_format(self, app_config: AppConfig):
        """Test requesting Mihomo format configuration."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1/config/mihomo",
                headers={"User-Agent": ALLOWED_BROWSER_UA},
            )

            assert response.status_code == 200
            assert response.mimetype == "application/yaml"
            assert b"proxies:" in response.data

    def test_direct_mihomo_format_alias(self, app_config: AppConfig):
        """Test requesting Mihomo format via direct alias."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1/mihomo",
                headers={"User-Agent": ALLOWED_BROWSER_UA},
            )

            assert response.status_code == 200
            assert response.mimetype == "application/yaml"
            assert b"proxies:" in response.data

    def test_mihomo_profile_selected_by_user_agent(self, app_config: AppConfig):
        """Matching Mihomo keyword profile should be used for response."""
        variant = app_config.mihomo_profile_file.parent / "mihomo_cmfa.yaml"
        variant.write_text(
            """profile: cmfa
proxy-template:
  type: vless
  servername: example.com
  reality-opts:
    public-key: ""
    short-id: ""
""",
            encoding="utf-8",
        )

        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1/mihomo",
                headers={"User-Agent": "Mozilla/5.0 cmfa/android"},
            )

            assert response.status_code == 200
            assert b"profile: cmfa" in response.data

    def test_v2ray_config_format(self, app_config: AppConfig):
        """Test requesting V2Ray format configuration."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1/sub/v2ray",
                headers={"User-Agent": ALLOWED_BROWSER_UA},
            )

            assert response.status_code == 200
            assert response.mimetype == "text/plain"
            assert b"vless://" in response.data

    def test_v2ray_profile_selected_by_user_agent(self, app_config: AppConfig):
        """Matching V2Ray keyword profile should be used for response."""
        variant = app_config.v2ray_profile_file.parent / "v2ray_android.lst"
        variant.write_text(
            "vless://<ID>@<ADDRESS>:443?type=tcp#android-<NAME>",
            encoding="utf-8",
        )

        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1/sub/v2ray",
                headers={"User-Agent": "Mozilla/5.0 cmfa/android"},
            )

            assert response.status_code == 200
            assert b"#android-" in response.data

    def test_json_config_format(self, app_config: AppConfig):
        """Test requesting JSON format configuration."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1/config/json",
                headers={"User-Agent": ALLOWED_BROWSER_UA},
            )

            assert response.status_code == 200
            assert response.mimetype == "application/json"
            assert response.data.startswith(b"[")

    def test_json_profile_selected_by_user_agent(self, app_config: AppConfig):
        """Matching Xray keyword profile should be used for response."""
        variant = app_config.xray_profile_file.parent / "xray_android.json"
        variant.write_text(
            """[
  {
    "remarks": "android",
    "outbounds": [
      {
        "protocol": "vless",
        "settings": {
          "address": null,
          "port": 443,
          "id": null
        }
      }
    ]
  }
]""",
            encoding="utf-8",
        )

        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1",
                headers={"User-Agent": "Mozilla/5.0 Android"},
            )

            assert response.status_code == 200
            assert b'"remarks": "Server 1 | android"' in response.data

    def test_invalid_user_returns_404(self, app_config: AppConfig):
        """Test that invalid user returns 404."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get("/secret/nonexistent_user")

            # App redirects to "/" on errors (404 becomes 302)
            assert response.status_code == 302

    def test_user_agent_logging(self, app_config: AppConfig):
        """Test that user agent is logged."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            # Request with specific user agent
            response = client.get(
                "/secret/user1",
                headers={"User-Agent": "Happ/4.7.1/ios/2604040141682"},
            )

            assert response.status_code == 200

    def test_x_forwarded_for_header(self, app_config: AppConfig):
        """Test X-Forwarded-For header processing."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1",
                headers={
                    "User-Agent": ALLOWED_BROWSER_UA,
                    "X-Forwarded-For": "203.0.113.1",
                },
            )

            assert response.status_code == 200

    def test_https_proxy_header(self, app_config: AppConfig):
        """Test HTTPS proxy headers."""
        app = create_app(app_config)
        client = app.test_client()

        # When X-Forwarded-Proto is https, should be allowed
        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1",
                headers={
                    "User-Agent": ALLOWED_BROWSER_UA,
                    "X-Forwarded-Proto": "https",
                },
            )

            assert response.status_code == 200

    def test_yandex_browser_user_agent_blocked(self, app_config: AppConfig):
        """Test that Yandex Browser is blocked by user-agent policy."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1",
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                        "(KHTML, like Gecko) Chrome/123.0.0.0 YaBrowser/24.4.1.0 Safari/537.36"
                    )
                },
            )

            # 403 is handled by redirecting to root
            assert response.status_code == 302


class TestUserAgentPolicy:
    """Tests for subscription user-agent allowlist/denylist policy."""

    def test_allows_common_browser(self):
        """Common browser user agents should be allowed."""
        ua = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        assert _is_allowed_subscription_user_agent(ua)

    def test_blocks_yandex_browser(self):
        """Yandex Browser user agents should be blocked."""
        ua = (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 YaBrowser/24.4.1.0 Safari/537.36"
        )
        assert not _is_allowed_subscription_user_agent(ua)

    def test_allows_happ_mobile_agents(self):
        """happ/android and happ/ios should be explicitly allowed."""
        assert _is_allowed_subscription_user_agent("happ/android")
        assert _is_allowed_subscription_user_agent("happ/ios")

    def test_allows_happ_full_client_agent(self):
        """Happ full client user agent with platform/build should be allowed."""
        assert _is_allowed_subscription_user_agent("Happ/4.7.1/ios/2604040141682")
        assert _is_allowed_subscription_user_agent("Happ/4.7.1/android/2604040141682")

    def test_blocks_legacy_happ_agent_without_platform(self):
        """Legacy Happ user agent without platform/build should be blocked."""
        assert not _is_allowed_subscription_user_agent("Happ/4.7.1")

    def test_allows_flclashx_platform_agents(self):
        """FlClash X user agents for all desktop platforms should be allowed."""
        assert _is_allowed_subscription_user_agent("FlClash X/v1.2.3 Platform/macos")
        assert _is_allowed_subscription_user_agent("FlClash X/v1.2.3 Platform/linux")
        assert _is_allowed_subscription_user_agent("FlClash X/v1.2.3 Platform/windows")

    def test_blocks_unknown_non_browser_client(self):
        """Unknown non-browser clients should be blocked by whitelist policy."""
        assert not _is_allowed_subscription_user_agent("curl/8.6.0")


class TestConfigGeneration:
    """Tests for configuration generation flow."""

    def test_generate_mihomo_for_valid_user(self, app_config: AppConfig):
        """Test generating Mihomo config for user with server access."""
        from src.services import ConfigService

        service = ConfigService(app_config)
        user = service.find_user("user1")

        assert user is not None

        servers = service.get_servers()
        # Filter servers user has access to
        eligible = [s for s in servers if not s.groups or user.has_access_to_groups(s.groups)]

        if eligible:
            result = service.build_mihomo_config(eligible, user)
            assert isinstance(result, bytes)
            assert len(result) > 0

    def test_generate_v2ray_for_valid_user(self, app_config: AppConfig):
        """Test generating V2Ray config for user with server access."""
        from src.services import ConfigService

        service = ConfigService(app_config)
        user = service.find_user("user1")

        assert user is not None

        servers = service.get_servers()
        # Filter servers user has access to
        eligible = [s for s in servers if not s.groups or user.has_access_to_groups(s.groups)]

        if eligible:
            result = service.build_v2ray_config(eligible, user)
            assert isinstance(result, bytes)
            assert len(result) > 0

    def test_no_servers_raises_error(self, app_config: AppConfig):
        """Test that building config with no servers raises error."""
        from src.builders import MihomoBuilder
        from src.models import UserInfo

        user = UserInfo(id="test-id", groups=frozenset(["admin"]))
        builder = MihomoBuilder(
            template_loader=lambda template_name=None, user_agent="": {"proxy-template": {}}
        )

        try:
            builder.build([], user)
            raise AssertionError("Expected ValueError for no servers")
        except ValueError:
            pass  # Expected
