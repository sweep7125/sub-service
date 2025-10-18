"""Pytest configuration and shared fixtures."""

import tempfile
from collections.abc import Generator
from pathlib import Path

import pytest

from src.models import AppConfig, Server, UserInfo
from src.utils import SpiderXGenerator


@pytest.fixture
def temp_dir() -> Generator[Path]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_users_file(temp_dir: Path) -> Path:
    """Create sample users file for testing."""
    users_file = temp_dir / "users"
    users_file.write_text(
        "# Users configuration\n"
        "550e8400-e29b-41d4-a716-446655440001|aabbccdd|user1|Test User 1|premium,vip\n"
        "550e8400-e29b-41d4-a716-446655440002|eeffgghh|user2|Test User 2|default\n"
        "550e8400-e29b-41d4-a716-446655440003|iijjkkll|user3|Test User 3|\n"
        "# Comment line\n"
        "550e8400-e29b-41d4-a716-446655440004||user4|User without short ID|premium\n",
        encoding="utf-8",
    )
    return users_file


@pytest.fixture
def sample_servers_file(temp_dir: Path) -> Path:
    """Create sample servers file for testing."""
    servers_file = temp_dir / "servers"
    servers_file.write_text(
        "# Servers configuration\n"
        "server1.example.com|sni1.example.com|https://dns.google/dns-query|pubkey1|Server 1|premium,vip|internal||\n"
        "server2.example.com|sni2.example.com||pubkey2|Server 2|default|internal||\n"
        "server3.example.com|||pubkey3|Server 3||internal||\n"
        "external.example.com|ext.example.com||pubkey4|External Server|premium|external|ext-uuid|ext-short\n",
        encoding="utf-8",
    )
    return servers_file


@pytest.fixture
def sample_v2ray_template(temp_dir: Path) -> Path:
    """Create sample V2Ray template file."""
    template_file = temp_dir / "v2ray-template.txt"
    template_file.write_text(
        "vless://<ID>@<ADDRESS>:443?encryption=none&flow=xtls-rprx-vision&"
        "security=reality&sni=<SERVERNAME>&fp=chrome&pbk=<PBK>&"
        "sid=<SHORTID>&spx=%2F<SPIDERX>&type=tcp&headerType=none#<NAME>",
        encoding="utf-8",
    )
    return template_file


@pytest.fixture
def sample_mihomo_template(temp_dir: Path) -> Path:
    """Create sample Mihomo template file."""
    template_file = temp_dir / "mihomo-template.yaml"
    template_file.write_text(
        """proxy-template:
  type: vless
  network: tcp
  udp: true
  tls: true
  servername: example.com
  reality-opts:
    public-key: ""
    short-id: ""
  client-fingerprint: chrome

proxy-groups:
  - name: auto
    type: url-test
    proxies: __PROXY_NAMES__
    url: http://www.gstatic.com/generate_204
    interval: 300

rules:
  - MATCH,auto
""",
        encoding="utf-8",
    )
    return template_file


@pytest.fixture
def sample_v2ray_json_template(temp_dir: Path) -> Path:
    """Create sample V2Ray JSON template file."""
    template_file = temp_dir / "v2ray-template.json"
    template_file.write_text(
        """{
  "log": {"loglevel": "warning"},
  "inbounds": [{"port": 1080, "protocol": "socks"}],
  "outbounds": [{
    "protocol": "vless",
    "settings": {
      "vnext": [{
        "address": "server.example.com",
        "port": 443,
        "users": [{"id": "uuid", "encryption": "none"}]
      }]
    }
  }]
}""",
        encoding="utf-8",
    )
    return template_file


@pytest.fixture
def app_config(
    temp_dir: Path,
    sample_users_file: Path,
    sample_servers_file: Path,
    sample_v2ray_template: Path,
    sample_mihomo_template: Path,
    sample_v2ray_json_template: Path,
) -> AppConfig:
    """Create AppConfig for testing."""
    happ_routing = temp_dir / "happ.routing"
    happ_routing.write_text("{}", encoding="utf-8")
    return AppConfig(
        base_dir=temp_dir,
        cache_dir=temp_dir / "cache",
        servers_file=sample_servers_file,
        users_file=sample_users_file,
        template_file=sample_v2ray_template,
        v2ray_template_file=sample_v2ray_json_template,
        mihomo_template_file=sample_mihomo_template,
        happ_routing_file=happ_routing,
        geo_cache_ttl=3600,
    )


@pytest.fixture
def sample_user() -> UserInfo:
    """Create sample UserInfo for testing."""
    return UserInfo(
        id="550e8400-e29b-41d4-a716-446655440000",
        short_id="12345678",
        spider_x="/test-path",
        comment="Test User",
        link_path="testuser",
        groups=frozenset(["premium", "vip"]),
    )


@pytest.fixture
def sample_server() -> Server:
    """Create sample Server for testing."""
    return Server(
        host="test.example.com",
        description="Test Server",
        alias="alias.example.com",
        dns_override="https://dns.google/dns-query",
        public_key="test-public-key",
        fixed_id=None,
        fixed_short_id=None,
        is_external=False,
        groups=frozenset(["premium", "vip"]),
    )


@pytest.fixture
def spiderx_generator() -> SpiderXGenerator:
    """Create SpiderXGenerator for testing."""
    return SpiderXGenerator()


@pytest.fixture
def multiple_servers() -> list[Server]:
    """Create list of sample servers with different configurations."""
    return [
        Server(
            host="server1.example.com",
            description="Premium Server 1",
            alias="sni1.example.com",
            public_key="key1",
            groups=frozenset(["premium"]),
        ),
        Server(
            host="server2.example.com",
            description="VIP Server",
            alias="sni2.example.com",
            public_key="key2",
            groups=frozenset(["vip"]),
        ),
        Server(
            host="server3.example.com",
            description="Default Server",
            public_key="key3",
            groups=frozenset(["default"]),
        ),
        Server(
            host="external.example.com",
            description="External Server",
            public_key="key4",
            is_external=True,
            fixed_id="ext-uuid",
            fixed_short_id="ext-short",
            groups=frozenset(["premium"]),
        ),
    ]
