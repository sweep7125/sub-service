"""Tests for environment-backed configuration helpers."""

from importlib import reload
from pathlib import Path


class TestEnvConfig:
    """Tests for environment configuration behavior."""

    def test_incy_routing_file_defaults_to_incy(self, monkeypatch):
        """Default Incy routing file should be separate from Happ."""
        monkeypatch.setenv("SECRET_PATH", "secret")
        monkeypatch.delenv("INCY_ROUTING_FILE", raising=False)

        from src import config as config_module

        reload(config_module)

        assert config_module.env_config.happ_routing_file.name == "happ.routing"
        assert config_module.env_config.incy_routing_file.name == "incy.routing"

    def test_constants_import_without_secret_path(self, monkeypatch):
        """Constants import should not require SECRET_PATH eagerly."""
        monkeypatch.delenv("SECRET_PATH", raising=False)

        from src import config as config_module
        from src import constants as constants_module

        reload(config_module)
        reload(constants_module)

        assert frozenset() == constants_module.RESERVED_PATHS
        assert constants_module.get_reserved_paths("secret") == frozenset({"secret", "/secret"})


class TestAppConfig:
    """Tests for application config model."""

    def test_from_environment_uses_override_base_dir(self, monkeypatch, temp_dir: Path):
        """Relative env paths should resolve against provided base_dir."""
        override_base = temp_dir / "override"
        templates_dir = override_base / "templates"
        templates_dir.mkdir(parents=True)

        (override_base / "servers").write_text("", encoding="utf-8")
        (override_base / "users").write_text("", encoding="utf-8")
        (templates_dir / "v2ray-url-template.txt").write_text("template", encoding="utf-8")
        (templates_dir / "v2ray-template.json").write_text("[]", encoding="utf-8")
        (templates_dir / "mihomo-template.yaml").write_text("{}", encoding="utf-8")
        (override_base / "happ.routing").write_text("{}", encoding="utf-8")
        (override_base / "incy.routing").write_text("{}", encoding="utf-8")

        other_base = temp_dir / "other"
        other_base.mkdir()

        monkeypatch.setenv("SECRET_PATH", "secret")
        monkeypatch.setenv("BASE_DIR", str(other_base))
        monkeypatch.setenv("SERVERS_FILE", "servers")
        monkeypatch.setenv("USERS_FILE", "users")
        monkeypatch.setenv("TEMPLATE_FILE", "templates/v2ray-url-template.txt")
        monkeypatch.setenv("HAPP_ROUTING_FILE", "happ.routing")
        monkeypatch.delenv("INCY_ROUTING_FILE", raising=False)

        from src.models import AppConfig

        config = AppConfig.from_environment(base_dir=override_base)

        assert config.base_dir == override_base
        assert config.servers_file == override_base / "servers"
        assert config.users_file == override_base / "users"
        assert config.template_file == override_base / "templates" / "v2ray-url-template.txt"
        assert config.happ_routing_file == override_base / "happ.routing"
        assert config.incy_routing_file == override_base / "incy.routing"
