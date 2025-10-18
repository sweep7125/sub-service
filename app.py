"""WSGI entry point for production deployment."""

import logging
import sys
from pathlib import Path

from waitress import serve

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import env_config
from src.models import AppConfig
from src.web import create_app


def setup_logging() -> None:
    """Configure logging for production application."""
    logging.basicConfig(
        level=getattr(logging, env_config.log_level, logging.INFO),
        format=env_config.log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,  # Override any existing configuration
    )


def main() -> None:
    """Run the application using Waitress WSGI server."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Create application
    config = AppConfig.from_environment()
    logger.info("Starting production server")
    logger.info(f"Base directory: {config.base_dir}")
    logger.info(f"Cache directory: {config.cache_dir}")

    app = create_app(config)

    # Get socket path from environment
    socket_path = env_config.socket_path
    if not socket_path:
        logger.error("SOCK environment variable is required")
        raise ValueError("SOCK environment variable is required")

    logger.info(f"Socket path: {socket_path}")
    logger.info(f"Worker threads: {env_config.worker_threads}")
    logger.info("Application ready to accept requests")

    # Serve application
    serve(
        app,
        unix_socket=socket_path,
        unix_socket_perms="0666",
        threads=env_config.worker_threads,
        ident="",
    )


if __name__ == "__main__":
    main()
