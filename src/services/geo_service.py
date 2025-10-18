"""Geo files update service."""

import base64
import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

from ..constants import GEO_FILES_URLS

logger = logging.getLogger(__name__)


class GeoFileService:
    """Service for managing geo files updates and caching.

    Handles checking for updates to geosite.dat and geoip.dat files
    with efficient caching to avoid excessive network requests.
    """

    def __init__(self, cache_dir: Path, cache_ttl: int = 600) -> None:
        """Initialize geo file service.

        Args:
            cache_dir: Directory for storing cache metadata
            cache_ttl: Cache TTL in seconds
        """
        self.cache_dir = cache_dir
        self.cache_ttl = cache_ttl
        self.meta_file = cache_dir / "geofiles_meta.json"

    def get_last_updated_timestamp(self) -> int:
        """Get timestamp of last geo files update.

        Returns:
            Unix timestamp of last update
        """
        metadata = self._load_metadata()
        now = int(time.time())
        last_check = int(metadata.get("last_check", 0))

        # Return cached value if still fresh
        if now - last_check < self.cache_ttl and "last_updated" in metadata:
            return int(metadata.get("last_updated", 0))

        # Check for updates
        last_updated = self._check_updates(metadata, now)
        return last_updated

    def build_routing_header(self, routing_template: dict[str, Any]) -> str:
        """Build routing header value for Happ clients.

        Args:
            routing_template: Routing configuration template

        Returns:
            Base64-encoded routing header value
        """
        template = routing_template.copy()
        timestamp = self.get_last_updated_timestamp()

        # Add timestamp to template
        template["LastUpdated"] = str(timestamp) if timestamp > 0 else ""

        try:
            json_str = json.dumps(template, ensure_ascii=False, separators=(",", ":"))
            b64 = base64.b64encode(json_str.encode("utf-8")).decode("ascii")
            return f"happ://routing/onadd/{b64}"
        except (TypeError, UnicodeEncodeError, ValueError) as e:
            logger.warning(f"Failed to build routing header: {e}")
            return ""

    def _load_metadata(self) -> dict[str, Any]:
        """Load metadata from cache file.

        Returns:
            Metadata dictionary
        """
        try:
            with self.meta_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError as e:
            logger.warning(f"Invalid JSON in metadata file: {e}")
            return {}
        except OSError as e:
            logger.warning(f"Failed to load metadata file: {e}")
            return {}

    def _save_metadata(self, metadata: dict[str, Any]) -> None:
        """Save metadata to cache file.

        Args:
            metadata: Metadata to save
        """
        try:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

            tmp_file = self.meta_file.with_suffix(self.meta_file.suffix + ".tmp")
            with tmp_file.open("w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # Safe file replacement (atomic on POSIX, best-effort on Windows)
            if self.meta_file.exists():
                try:
                    tmp_file.replace(self.meta_file)
                except OSError:
                    # On Windows, replace may fail if file is open
                    self.meta_file.unlink()
                    tmp_file.rename(self.meta_file)
            else:
                tmp_file.rename(self.meta_file)
        except OSError as e:
            logger.warning(f"Failed to save metadata: {e}")

    def _check_updates(self, metadata: dict[str, Any], now: int) -> int:
        """Check for geo files updates.

        Args:
            metadata: Current metadata
            now: Current timestamp

        Returns:
            Last updated timestamp
        """
        session = requests.Session()
        session.headers.update({"User-Agent": "happ-routing/1.0"})

        max_timestamp = int(metadata.get("last_updated", 0))
        url_metadata = metadata.get("urls", {})

        # Check each geo file URL
        for url in GEO_FILES_URLS:
            timestamp = self._check_url(session, url, url_metadata.get(url, {}), now)
            max_timestamp = max(max_timestamp, timestamp)

            # Update URL metadata
            url_metadata[url] = {
                "last_ts": timestamp,
                "etag": url_metadata.get(url, {}).get("etag"),
            }

        # Save updated metadata
        metadata["last_check"] = now
        metadata["last_updated"] = max_timestamp
        metadata["urls"] = url_metadata
        self._save_metadata(metadata)

        return max_timestamp

    def _check_url(
        self, session: requests.Session, url: str, url_meta: dict[str, Any], now: int
    ) -> int:
        """Check a single URL for updates.

        Args:
            session: Requests session
            url: URL to check
            url_meta: Metadata for this URL
            now: Current timestamp

        Returns:
            Timestamp for this URL
        """
        prev_etag = url_meta.get("etag")
        prev_ts = int(url_meta.get("last_ts", 0))

        headers = {}
        if prev_etag:
            headers["If-None-Match"] = prev_etag

        try:
            with session.get(url, headers=headers, timeout=15, stream=True) as response:
                if response.status_code == 304:
                    # Not modified
                    return prev_ts if prev_ts > 0 else now

                elif response.status_code == 200:
                    # Check ETag for changes
                    etag = response.headers.get("ETag")

                    if etag and etag != prev_etag:
                        # Content changed
                        url_meta["etag"] = etag
                        return now
                    elif etag and not prev_etag:
                        # First time seeing ETag
                        url_meta["etag"] = etag
                        return now
                    else:
                        # No ETag change
                        return prev_ts if prev_ts > 0 else now

                else:
                    # Error response, use previous timestamp
                    return prev_ts

        except (requests.RequestException, requests.Timeout) as e:
            logger.warning(f"Failed to check URL {url}: {e}")
            return prev_ts
