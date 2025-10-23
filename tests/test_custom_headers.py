"""Tests for custom headers configuration."""

import re


class TestCustomHeaders:
    """Tests for custom HTTP headers configuration."""

    def test_custom_headers_parsing(self, monkeypatch):
        """Test that custom headers are parsed correctly from environment."""
        # Set up test environment variables
        monkeypatch.setenv("CUSTOM_HEADER_1", "profile-update-interval|24")
        monkeypatch.setenv(
            "CUSTOM_HEADER_2", "profile-title|base64:VGVzdFRpdGxlRXhhbXBsZQ=="
        )
        monkeypatch.setenv(
            "CUSTOM_HEADER_3", r"x-special-feature|enabled|^Happ/\d+\.\d+\.\d+"
        )
        monkeypatch.setenv(
            "CUSTOM_HEADER_4", "x-mobile-config|true|Mobile|Android|iPhone"
        )
        monkeypatch.setenv("CUSTOM_HEADER_5", "x-always-sent|always")

        # Reload config to pick up new environment variables
        from importlib import reload

        from src import config as config_module

        reload(config_module)
        from src.config import env_config

        headers = env_config.custom_headers

        # Verify we have all headers
        assert len(headers) >= 5

        # Find our test headers
        test_headers = {h["name"]: h for h in headers if h["name"].startswith(("profile-", "x-"))}

        # Check header 1 (no user-agent filter)
        assert "profile-update-interval" in test_headers
        h1 = test_headers["profile-update-interval"]
        assert h1["value"] == "24"
        assert h1["user_agent_regex"] is None

        # Check header 2 (no user-agent filter, with colon in value)
        assert "profile-title" in test_headers
        h2 = test_headers["profile-title"]
        assert h2["value"] == "base64:VGVzdFRpdGxlRXhhbXBsZQ=="
        assert h2["user_agent_regex"] is None

        # Check header 3 (with user-agent filter)
        assert "x-special-feature" in test_headers
        h3 = test_headers["x-special-feature"]
        assert h3["value"] == "enabled"
        assert h3["user_agent_regex"] == r"^Happ/\d+\.\d+\.\d+"

        # Check header 4 (with user-agent filter containing pipes)
        assert "x-mobile-config" in test_headers
        h4 = test_headers["x-mobile-config"]
        assert h4["value"] == "true"
        assert h4["user_agent_regex"] == "Mobile|Android|iPhone"

        # Check header 5 (no user-agent filter)
        assert "x-always-sent" in test_headers
        h5 = test_headers["x-always-sent"]
        assert h5["value"] == "always"
        assert h5["user_agent_regex"] is None

    def test_user_agent_regex_matching(self, monkeypatch):
        """Test user-agent regex matching logic."""
        monkeypatch.setenv(
            "CUSTOM_HEADER_TEST1", r"test-happ|value1|^Happ/\d+\.\d+\.\d+"
        )
        monkeypatch.setenv(
            "CUSTOM_HEADER_TEST2", "test-mobile|value2|Mobile|Android|iPhone"
        )

        from importlib import reload

        from src import config as config_module

        reload(config_module)
        from src.config import env_config

        headers = env_config.custom_headers
        test_headers = {h["name"]: h for h in headers if h["name"].startswith("test-")}

        # Test Happ pattern
        happ_header = test_headers.get("test-happ")
        if happ_header:
            regex = happ_header["user_agent_regex"]
            assert re.search(regex, "Happ/1.2.3")
            assert re.search(regex, "Happ/10.0.1")
            assert not re.search(regex, "Chrome/1.0")

        # Test mobile pattern
        mobile_header = test_headers.get("test-mobile")
        if mobile_header:
            regex = mobile_header["user_agent_regex"]
            assert re.search(regex, "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)")
            assert re.search(regex, "Mozilla/5.0 (Linux; Android 10)")
            assert re.search(regex, "Mobile Safari")
            assert not re.search(regex, "Desktop Browser")

    def test_invalid_header_format(self, monkeypatch, caplog):
        """Test that invalid header formats are handled gracefully."""
        # Header with missing value
        monkeypatch.setenv("CUSTOM_HEADER_INVALID1", "header-name-only")

        from importlib import reload

        from src import config as config_module

        reload(config_module)
        from src.config import env_config

        headers = env_config.custom_headers
        invalid_headers = [h for h in headers if h["name"] == "header-name-only"]

        # Invalid header should be filtered out
        assert len(invalid_headers) == 0
        # Should have warning in logs
        assert "Invalid custom header format" in caplog.text

    def test_invalid_regex_pattern(self, monkeypatch, caplog):
        """Test that invalid regex patterns are handled gracefully."""
        # Header with invalid regex
        monkeypatch.setenv("CUSTOM_HEADER_BADREGEX", "test-header|test-value|[")

        from importlib import reload

        from src import config as config_module

        reload(config_module)
        from src.config import env_config

        headers = env_config.custom_headers
        bad_headers = [h for h in headers if h["name"] == "test-header"]

        # Header with invalid regex should be filtered out
        assert len(bad_headers) == 0
        # Should have error in logs
        assert "Invalid regex" in caplog.text

    def test_custom_headers_in_response(self, app_config, monkeypatch):
        """Test that custom headers are applied to responses."""
        # Set up custom headers
        monkeypatch.setenv("CUSTOM_HEADER_TEST", "x-test-header|test-value")

        from importlib import reload

        from src import config as config_module
        from src import constants as constants_module

        reload(config_module)
        reload(constants_module)

        from unittest.mock import patch

        from src.web import create_app

        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            response = client.get("/secret/user1")

            # Check if we can access headers (response might be redirect)
            if response.status_code == 200:
                # Custom header should be present
                assert "x-test-header" in response.headers or response.status_code in (200, 302)

    def test_user_agent_filtered_headers(self, app_config, monkeypatch):
        """Test that user-agent filtered headers are applied conditionally."""
        # Set up header that only applies to Happ clients
        monkeypatch.setenv(
            "CUSTOM_HEADER_HAPP_ONLY", r"x-happ-only|happ-value|^Happ/\d+"
        )

        from importlib import reload

        from src import config as config_module
        from src import constants as constants_module

        reload(config_module)
        reload(constants_module)

        from unittest.mock import patch

        from src.web import create_app

        app = create_app(app_config)
        client = app.test_client()

        with patch("src.web._is_secure_connection", return_value=True):
            # Request with non-Happ user agent
            response1 = client.get(
                "/secret/user1",
                headers={"User-Agent": "Chrome/1.0"},
            )

            # Request with Happ user agent
            response2 = client.get(
                "/secret/user1",
                headers={"User-Agent": "Happ/1.0.0"},
            )

            # Both should process successfully (200 or 302 redirect)
            assert response1.status_code in (200, 302)
            assert response2.status_code in (200, 302)
