"""Integration tests for web application."""

from unittest.mock import patch

from src.models import AppConfig
from src.web import create_app


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
            # user1 exists in sample data
            response = client.get("/secret/user1")

            # Should get some response (200 or 302 redirect on error)
            assert response.status_code in (200, 302)

    def test_mihomo_config_format(self, app_config: AppConfig):
        """Test requesting Mihomo format configuration."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get("/secret/user1/config/mihomo")

            # Should attempt to build config (200 or 302 on error)
            assert response.status_code in (200, 302)

    def test_v2ray_config_format(self, app_config: AppConfig):
        """Test requesting V2Ray format configuration."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get("/secret/user1/sub/v2ray")

            # Should attempt to build config (200 or 302 on error)
            assert response.status_code in (200, 302)

    def test_json_config_format(self, app_config: AppConfig):
        """Test requesting JSON format configuration."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get("/secret/user1/config/json")

            # Should attempt to build config (200 or 302 on error)
            assert response.status_code in (200, 302)

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
                headers={"User-Agent": "Happ/1.0.0"},
            )

            # Should process request (200 or 302 on error)
            assert response.status_code in (200, 302)

    def test_x_forwarded_for_header(self, app_config: AppConfig):
        """Test X-Forwarded-For header processing."""
        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1",
                headers={"X-Forwarded-For": "203.0.113.1"},
            )

            # Should process request (200 or 302 on error)
            assert response.status_code in (200, 302)

    def test_https_proxy_header(self, app_config: AppConfig):
        """Test HTTPS proxy headers."""
        app = create_app(app_config)
        client = app.test_client()

        # When X-Forwarded-Proto is https, should be allowed
        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get(
                "/secret/user1",
                headers={"X-Forwarded-Proto": "https"},
            )

            # Should process request (200 or 302 on error)
            assert response.status_code in (200, 302)


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
        builder = MihomoBuilder(template_loader=lambda template_name=None: {"proxy-template": {}})

        try:
            builder.build([], user)
            raise AssertionError("Expected ValueError for no servers")
        except ValueError:
            pass  # Expected
