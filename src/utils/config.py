"""Configuration management for Cascadia geospatial data integration system."""

import os
from pathlib import Path
from typing import Dict, Any

class Config:
    """Central configuration management with environment-aware settings."""

    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "data"
        self.raw_data_dir = self.data_dir / "raw"
        self.processed_data_dir = self.data_dir / "processed"
        self.cache_dir = self.data_dir / "cache"

        # Ensure directories exist
        for directory in [self.raw_data_dir, self.processed_data_dir, self.cache_dir]:
            directory.mkdir(parents=True, exist_ok=True)

    @property
    def h3_resolution(self) -> int:
        """Default H3 resolution for spatial indexing."""
        return int(os.getenv("H3_RESOLUTION", "9"))

    @property
    def max_download_retries(self) -> int:
        """Maximum retry attempts for data downloads."""
        return int(os.getenv("MAX_DOWNLOAD_RETRIES", "3"))

    @property
    def request_timeout(self) -> int:
        """Request timeout in seconds."""
        return int(os.getenv("REQUEST_TIMEOUT", "30"))

    @property
    def data_sources(self) -> Dict[str, Dict[str, Any]]:
        """Configuration for different data sources."""
        return {
            "world_cities": {
                "url": "https://raw.githubusercontent.com/datasets/world-cities/master/data/world-cities.csv",
                "format": "csv",
                "description": "World cities dataset with population data",
                "has_coordinates": True,
                "lat_column": "lat",
                "lon_column": "lng",
                "value_column": "population"
            },
            "us_states": {
                "url": "https://raw.githubusercontent.com/PublicaMundi/MappingAPI/master/data/geojson/us-states.json",
                "format": "geojson",
                "description": "US States boundaries",
                "has_coordinates": False,
                "value_column": "density"
            },
            "earthquakes": {
                "url": "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_week.geojson",
                "format": "geojson",
                "description": "Recent earthquakes (last 7 days)",
                "has_coordinates": True,
                "value_column": "mag"
            }
        }

    def get_cache_path(self, data_source: str) -> Path:
        """Get cache file path for a data source."""
        return self.cache_dir / f"{data_source}_processed.h3"

    def get_raw_data_path(self, data_source: str, extension: str = "geojson") -> Path:
        """Get raw data file path for a data source."""
        return self.raw_data_dir / f"{data_source}.{extension}"

    def get_processed_data_path(self, data_source: str) -> Path:
        """Get processed data file path for a data source."""
        return self.processed_data_dir / f"{data_source}_processed.h3"

# Global configuration instance
config = Config()

# Centralized logging configuration
def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Set up centralized logging configuration with best practices."""
    import logging
    from logging.handlers import RotatingFileHandler

    # Create logger hierarchy
    logger = logging.getLogger('cascadia')
    logger.setLevel(getattr(logging, log_level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler with rotation if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # Prevent duplicate logs
    logger.propagate = False

    return logger

# Global logger instance
logger = setup_logging()
