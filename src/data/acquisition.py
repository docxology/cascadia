"""Data acquisition module for downloading and retrieving geospatial data sources."""

import requests
import hashlib
import time
import json
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import logging
import mimetypes

from ..utils.config import config, logger

class DataAcquirer:
    """Handles data downloading and retrieval with caching and retry logic."""

    def __init__(self):
        self.session = requests.Session()
        self.request_timeout = config.request_timeout

        # Set proper headers to avoid blocking
        self.session.headers.update({
            'User-Agent': 'Cascadia-GeoData-Acquirer/1.0',
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })

    def calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file for integrity checking."""
        if not file_path.exists():
            return ""

        hash_sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_sha256.update(chunk)
        return hash_sha256.hexdigest()

    def download_file(self, url: str, destination: Path,
                     max_retries: Optional[int] = None) -> Tuple[bool, Dict[str, Any]]:
        """Download file from URL with enhanced error handling and validation."""
        if max_retries is None:
            max_retries = config.max_download_retries

        download_info = {
            'url': url,
            'attempts': 0,
            'total_size': 0,
            'downloaded_size': 0,
            'error': None,
            'content_type': None,
            'status_code': None
        }

        for attempt in range(max_retries):
            download_info['attempts'] = attempt + 1

            try:
                logger.info(f"Downloading {url} (attempt {attempt + 1}/{max_retries})")

                # Validate URL format
                if not self._is_valid_url(url):
                    download_info['error'] = f"Invalid URL format: {url}"
                    continue

                # Make request with timeout and proper headers
                response = self.session.get(url, stream=True, allow_redirects=True,
                                            timeout=self.request_timeout)
                download_info['status_code'] = response.status_code
                download_info['content_type'] = response.headers.get('content-type', '')

                # Check response status
                if not response.ok:
                    download_info['error'] = f"HTTP {response.status_code}: {response.reason}"
                    logger.warning(f"HTTP error {response.status_code} for {url}")
                    if attempt < max_retries - 1:
                        time.sleep(2 ** attempt)
                    continue

                # Validate content type if specified
                if not self._is_valid_content_type(url, response.headers):
                    download_info['error'] = f"Unexpected content type: {response.headers.get('content-type', 'unknown')}"
                    continue

                # Get file size if available
                total_size = response.headers.get('content-length')
                if total_size:
                    download_info['total_size'] = int(total_size)

                # Download with progress tracking and validation
                success, download_size = self._download_with_progress(
                    response, destination, download_info
                )

                if success:
                    # Validate downloaded file
                    if self._validate_downloaded_file(destination, download_info):
                        logger.info(f"Successfully downloaded {download_size} bytes to {destination}")
                        download_info['downloaded_size'] = download_size
                        return True, download_info
                    else:
                        download_info['error'] = "File validation failed"
                        logger.error(f"File validation failed for {destination}")

                if attempt < max_retries - 1:
                    logger.warning(f"Download attempt {attempt + 1} failed, retrying...")
                    time.sleep(min(2 ** attempt, 60))  # Cap exponential backoff at 60 seconds
                else:
                    download_info['error'] = f"Download failed after {max_retries} attempts"

            except requests.exceptions.Timeout:
                download_info['error'] = "Request timeout"
                logger.warning(f"Timeout on attempt {attempt + 1} for {url}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

            except requests.exceptions.ConnectionError:
                download_info['error'] = "Connection error"
                logger.warning(f"Connection error on attempt {attempt + 1} for {url}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

            except requests.exceptions.HTTPError as e:
                download_info['error'] = f"HTTP error: {e}"
                logger.warning(f"HTTP error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

            except Exception as e:
                download_info['error'] = f"Unexpected error: {str(e)}"
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)

        logger.error(f"Failed to download {url} after {max_retries} attempts")
        return False, download_info

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format and safety."""
        if not url or not isinstance(url, str):
            return False

        # Basic URL validation
        if not (url.startswith('http://') or url.startswith('https://')):
            return False

        # Check for potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'"]
        if any(char in url for char in dangerous_chars):
            return False

        return True

    def _is_valid_content_type(self, url: str, headers: Dict[str, str]) -> bool:
        """Validate content type matches expected format."""
        content_type = headers.get('content-type', '').lower()

        # Guess expected content type from URL
        expected_type, _ = mimetypes.guess_type(url)

        if expected_type:
            # Allow some flexibility in content type matching
            if 'json' in expected_type and 'json' in content_type:
                return True
            if 'csv' in expected_type and ('csv' in content_type or 'text' in content_type):
                return True
            if 'geojson' in expected_type and ('json' in content_type or 'geojson' in content_type):
                return True

        # If we can't determine expected type, be more lenient
        return True

    def _download_with_progress(self, response, destination: Path,
                               download_info: Dict[str, Any]) -> Tuple[bool, int]:
        """Download file with progress tracking."""
        downloaded_size = 0
        chunk_size = 8192

        try:
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        downloaded_size += len(chunk)

                        # Log progress for large files
                        if download_info['total_size'] > 1024 * 1024:  # > 1MB
                            if downloaded_size % (1024 * 1024) == 0:  # Every MB
                                progress = (downloaded_size / download_info['total_size']) * 100
                                logger.debug(f"Download progress: {progress:.1f}%")

            return True, downloaded_size

        except Exception as e:
            logger.error(f"Error writing to file {destination}: {e}")
            # Clean up partial download
            if destination.exists():
                destination.unlink()
            return False, 0

    def _validate_downloaded_file(self, file_path: Path, download_info: Dict[str, Any]) -> bool:
        """Validate downloaded file integrity and safety."""
        try:
            # Check file size
            if file_path.stat().st_size == 0:
                logger.error("Downloaded file is empty")
                return False

            # Check if file is too large (prevent DoS)
            max_size = 100 * 1024 * 1024  # 100MB limit
            if file_path.stat().st_size > max_size:
                logger.error(f"Downloaded file too large: {file_path.stat().st_size} bytes")
                return False

            # Basic content validation for known formats
            if file_path.suffix.lower() == '.json' or file_path.suffix.lower() == '.geojson':
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        # Try to parse JSON to validate format
                        json.load(f)
                except (json.JSONDecodeError, UnicodeDecodeError) as e:
                    logger.error(f"Invalid JSON content: {e}")
                    return False

            elif file_path.suffix.lower() == '.csv':
                try:
                    import pandas as pd
                    # Try to read CSV to validate format
                    pd.read_csv(file_path, nrows=5)  # Just read first few rows
                except Exception as e:
                    logger.error(f"Invalid CSV content: {e}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating file {file_path}: {e}")
            return False

    def acquire_data_source(self, data_source_name: str,
                           force_download: bool = False) -> Optional[Path]:
        """Acquire data for a specific source with enhanced error handling."""
        if data_source_name not in config.data_sources:
            logger.error(f"Unknown data source: {data_source_name}")
            return None

        source_config = config.data_sources[data_source_name]
        url = source_config['url']
        file_format = source_config['format']

        destination = config.get_raw_data_path(data_source_name, file_format)

        # Check if file exists and skip download if not forcing
        if destination.exists() and not force_download:
            logger.info(f"Data already exists at {destination}, skipping download")
            return destination

        # Ensure parent directory exists
        destination.parent.mkdir(parents=True, exist_ok=True)

        # Download the file with enhanced error handling
        success, download_info = self.download_file(url, destination)

        if success:
            logger.info(f"Successfully acquired {data_source_name} data")
            logger.debug(f"Download stats: {download_info}")
            return destination
        else:
            logger.error(f"Failed to acquire data for {data_source_name}: {download_info.get('error', 'Unknown error')}")
            return None

    def acquire_all_sources(self, force_download: bool = False) -> Dict[str, Optional[Path]]:
        """Acquire data for all configured sources."""
        results = {}

        for source_name in config.data_sources.keys():
            file_path = self.acquire_data_source(source_name, force_download)
            results[source_name] = file_path

        return results

    def validate_data_integrity(self, file_path: Path,
                               expected_hash: Optional[str] = None) -> bool:
        """Validate data integrity using hash comparison."""
        if not file_path.exists():
            return False

        actual_hash = self.calculate_file_hash(file_path)

        if expected_hash and actual_hash != expected_hash:
            logger.warning(f"Hash mismatch for {file_path}")
            return False

        return True

    def get_data_info(self, data_source_name: str) -> Optional[Dict[str, Any]]:
        """Get information about acquired data."""
        if data_source_name not in config.data_sources:
            return None

        file_path = config.get_raw_data_path(
            data_source_name,
            config.data_sources[data_source_name]['format']
        )

        if not file_path.exists():
            return None

        return {
            'source_name': data_source_name,
            'file_path': file_path,
            'file_size': file_path.stat().st_size,
            'last_modified': file_path.stat().st_mtime,
            'hash': self.calculate_file_hash(file_path),
            'config': config.data_sources[data_source_name]
        }
