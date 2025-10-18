"""Main entry point for development and testing."""

import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.config import env_config
from src.models import AppConfig
from src.web import create_app


def setup_logging() -> None:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, env_config.log_level, logging.INFO),
        format=env_config.log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
    )


def main() -> None:
    """Run the application in development mode."""
    setup_logging()
    logger = logging.getLogger(__name__)

    # Load configuration
    config = AppConfig.from_environment()
    logger.info(f"Base directory: {config.base_dir}")
    logger.info(f"Cache directory: {config.cache_dir}")

    # Create application
    app = create_app(config)

    # Run development server
    host = env_config.dev_host
    port = env_config.dev_port
    debug = env_config.dev_debug

    logger.info(f"Starting development server on http://{host}:{port}")
    logger.info(f"Secret path: /{env_config.secret_path}/")
    app.run(host=host, port=port, debug=debug)


if __name__ == "__main__":
    main()
