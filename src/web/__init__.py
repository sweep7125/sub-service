"""Web routes and HTTP handlers."""

import json
import logging
import re
import time
from typing import Final

from flask import Flask, Request, Response, abort, g, redirect, request

from ..config import env_config
from ..constants import (
    DEFAULT_PROFILE_TITLE,
    MIME_TYPE_JSON,
    MIME_TYPE_TEXT,
    MIME_TYPE_YAML,
    PROFILE_UPDATE_INTERVAL,
)
from ..models import AppConfig
from ..services import ConfigService, GeoFileService
from ..utils import get_client_ip

logger = logging.getLogger(__name__)


def _is_secure_connection(request_obj: Request) -> bool:
    """Check if connection is from localhost or through HTTPS reverse proxy.

    Args:
        request_obj: Flask request object

    Returns:
        True if connection is secure (localhost or HTTPS proxy), False otherwise
    """
    # Check if direct connection from localhost
    remote_addr = request_obj.remote_addr
    if remote_addr in ("127.0.0.1", "::1", "localhost"):
        logger.debug(f"Access allowed: localhost connection from {remote_addr}")
        return True

    # SECURITY FIX: Only trust X-Forwarded-Proto if connection is from localhost
    # This prevents header spoofing from external connections
    # In production, nginx should be on localhost connecting via Unix socket
    if remote_addr not in ("127.0.0.1", "::1", "localhost"):
        logger.warning(
            f"Access denied: non-localhost connection attempting to use proxy headers - "
            f"Remote: {remote_addr}"
        )
        return False

    # Check if behind HTTPS reverse proxy (nginx with SSL certificate)
    forwarded_proto = request_obj.headers.get("X-Forwarded-Proto", "").lower()
    if forwarded_proto == "https":
        logger.debug("Access allowed: HTTPS reverse proxy connection")
        return True

    logger.warning(
        f"Access denied: insecure connection - "
        f"Remote: {remote_addr}, "
        f"Proto: {forwarded_proto or 'none'}"
    )
    return False

# Happ client user agent pattern
_HAPP_USER_AGENT_PATTERN: Final[re.Pattern[str]] = re.compile(r"^Happ/\d+\.\d+\.\d+")


class WebApplication:
    """Main web application for VPN/Proxy configuration distribution."""

    def __init__(self, config: AppConfig) -> None:
        """Initialize web application.

        Args:
            config: Application configuration
        """
        self.config = config
        self.config_service = ConfigService(config)
        self.geo_service = GeoFileService(
            cache_dir=config.cache_dir, cache_ttl=config.geo_cache_ttl
        )

        # Initialize Flask app
        self.app = Flask(__name__)
        self.app.config["JSON_SORT_KEYS"] = env_config.flask_json_sort_keys

        # Register middleware
        self._register_middleware()

        # Register routes
        self._register_routes()

        # Load Happ routing config
        self._happ_routing_config = self._load_happ_routing()

    def _register_middleware(self) -> None:
        """Register Flask middleware for logging."""

        @self.app.before_request
        def before_request() -> None:
            """Log incoming request and store request start time."""
            g.start_time = time.time()
            g.client_ip = get_client_ip(request)

            # Security check: only allow localhost or HTTPS reverse proxy
            if not _is_secure_connection(request):
                logger.warning(
                    f"Security: blocked insecure connection - "
                    f"Path: {request.path} - IP: {g.client_ip}"
                )
                abort(403)

            # Log all incoming requests at DEBUG level
            logger.debug(
                f"Incoming request: {request.method} {request.path} "
                f"from {g.client_ip} - UA: {request.headers.get('User-Agent', 'N/A')}"
            )

        @self.app.after_request
        def after_request(response: Response) -> Response:
            """Log response details after request processing."""
            duration = time.time() - getattr(g, "start_time", time.time())
            client_ip = getattr(g, "client_ip", "unknown")

            # Log response at INFO or WARNING level depending on status
            if response.status_code < 400:
                logger.info(
                    f"{request.method} {request.path} - "
                    f"Status: {response.status_code} - "
                    f"IP: {client_ip} - "
                    f"Duration: {duration:.3f}s"
                )
            else:
                logger.warning(
                    f"{request.method} {request.path} - "
                    f"Status: {response.status_code} - "
                    f"IP: {client_ip} - "
                    f"Duration: {duration:.3f}s"
                )

            return response

    def _register_routes(self) -> None:
        """Register all application routes."""
        # Get secret path from environment
        secret_path = env_config.secret_path

        # Main entry point
        self.app.route(f"/{secret_path}/", defaults={"user_path": ""})(self.handle_request)

        self.app.route(f"/{secret_path}/<path:user_path>")(self.handle_request)

        # Error handlers
        for error_code in (403, 404, 500):
            self.app.errorhandler(error_code)(self.handle_error)

        self.app.errorhandler(Exception)(self.handle_error)

    def handle_request(self, user_path: str) -> Response:
        """Handle configuration request.

        Args:
            user_path: User-specific path segment

        Returns:
            Configuration response
        """
        client_ip = getattr(g, "client_ip", "unknown")
        user_agent = request.headers.get('User-Agent', 'N/A')

        # Parse user path
        user, format_type = self._parse_user_path(user_path)

        # Get servers
        servers = self.config_service.get_servers()

        # Check if servers available
        if not servers:
            logger.error(f"No servers available in configuration - IP: {client_ip}")
            abort(503)  # Service Unavailable

        # Log successful config generation
        logger.info(
            f"Generating config for user '{user.comment}' "
            f"(ID: {user.id[:8]}...) - "
            f"Format: {format_type} - "
            f"IP: {client_ip} - "
            f"UA: {user_agent} - "
            f"Groups: {', '.join(user.groups)}"
        )

        # Generate appropriate configuration
        try:
            if format_type == "v2ray":
                return self._build_v2ray_response(servers, user)

            elif format_type == "mihomo":
                return self._build_mihomo_response(servers, user)

            else:  # json or default
                return self._build_json_response(servers, user)

        except ValueError as e:
            # User has no access to any servers
            logger.warning(f"Cannot build config: {e} - IP: {client_ip}")
            abort(403)

    def handle_error(self, error):
        """Handle errors by redirecting to root.

        Args:
            error: Error that occurred

        Returns:
            Redirect response
        """
        client_ip = getattr(g, "client_ip", "unknown")
        error_code = getattr(error, "code", 500)

        # Log the error with details
        if error_code == 403:
            logger.warning(
                f"Access denied - Path: {request.path} - IP: {client_ip} - "
                f"UA: {request.headers.get('User-Agent', 'N/A')}"
            )
        elif error_code == 404:
            logger.info(f"Not found - Path: {request.path} - IP: {client_ip}")
        else:
            logger.error(
                f"Server error ({error_code}) - Path: {request.path} - "
                f"IP: {client_ip} - Error: {error}",
                exc_info=error_code == 500,
            )

        return redirect("/")

    def _parse_user_path(self, user_path: str) -> tuple:
        """Parse user path to extract user and format.

        Args:
            user_path: Path segment after base URL

        Returns:
            Tuple of (user, format_type)

        Raises:
            403: If user not found
        """
        client_ip = getattr(g, "client_ip", "unknown")
        segments = [s for s in user_path.split("/") if s]

        # First segment is user lookup key
        lookup_key = segments[0] if segments else ""
        if not lookup_key:
            logger.warning(f"Empty user path - IP: {client_ip}")
            abort(403)

        # Find user
        user = self.config_service.find_user(lookup_key)
        if not user:
            logger.warning(f"User not found: '{lookup_key}' - IP: {client_ip}")
            abort(403)

        # Determine format type
        format_type = "json"  # default
        if len(segments) > 1:
            format_segment = segments[1].lower()

            if format_segment == "v2ray":
                format_type = "v2ray"
            elif format_segment in ("clash", "mh", "type3"):
                format_type = "mihomo"
            elif format_segment == "json":
                format_type = "json"

        return user, format_type

    def _build_v2ray_response(self, servers, user) -> Response:
        """Build V2Ray subscription response.

        Args:
            servers: Available servers
            user: User credentials

        Returns:
            Text response with subscription links
        """
        content = self.config_service.build_v2ray_config(servers, user)
        response = Response(content, mimetype=MIME_TYPE_TEXT)
        return self._apply_headers(response)

    def _build_mihomo_response(self, servers, user) -> Response:
        """Build Mihomo/Clash configuration response.

        Args:
            servers: Available servers
            user: User credentials

        Returns:
            YAML file response
        """
        content = self.config_service.build_mihomo_config(servers, user)
        response = Response(content, mimetype=MIME_TYPE_YAML)
        response = self._apply_headers(response)

        # Add attachment header
        response.headers["content-disposition"] = 'attachment; filename="sub"'

        return response

    def _build_json_response(self, servers, user) -> Response:
        """Build legacy JSON configuration response.

        Args:
            servers: Available servers
            user: User credentials

        Returns:
            JSON response
        """
        content = self.config_service.build_legacy_config(servers, user)
        response = Response(content, mimetype=MIME_TYPE_JSON)
        return self._apply_headers(response)

    def _apply_headers(self, response: Response) -> Response:
        """Apply common headers to response.

        Args:
            response: Response to modify

        Returns:
            Modified response
        """
        # Standard headers
        response.headers["profile-update-interval"] = PROFILE_UPDATE_INTERVAL
        response.headers["profile-title"] = DEFAULT_PROFILE_TITLE

        # Happ routing header for compatible clients
        user_agent = request.headers.get("User-Agent", "")
        if _HAPP_USER_AGENT_PATTERN.match(user_agent):
            routing_header = self.geo_service.build_routing_header(self._happ_routing_config)
            if routing_header:
                response.headers["routing"] = routing_header

        return response

    def _load_happ_routing(self) -> dict:
        """Load Happ routing configuration.

        Returns:
            Routing configuration dictionary
        """
        try:
            with self.config.happ_routing_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except FileNotFoundError:
            logger.info("Happ routing file not found, using empty configuration")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in happ routing file: {e}")
            return {}
        except OSError as e:
            logger.error(f"Failed to load happ routing file: {e}")
            return {}


def create_app(config: AppConfig | None = None) -> Flask:
    """Create and configure Flask application.

    Args:
        config: Application configuration (or None to load from environment)

    Returns:
        Configured Flask application
    """
    if config is None:
        config = AppConfig.from_environment()

    web_app = WebApplication(config)
    return web_app.app
