"""Tests for the configuration module."""

import pytest
from pathlib import Path
import tempfile
import os

from src.utils.config import Config

class TestConfig:
    """Test cases for the Config class."""

    def test_config_initialization(self):
        """Test that Config initializes with correct paths."""
        config = Config()

        # Test that project root is correctly identified
        assert config.project_root.exists()
        assert config.project_root.is_dir()

        # Test data directories exist or can be created
        assert config.data_dir.exists()
        assert config.raw_data_dir.exists()
        assert config.processed_data_dir.exists()
        assert config.cache_dir.exists()

    def test_h3_resolution_default(self):
        """Test default H3 resolution."""
        config = Config()
        assert config.h3_resolution == 9

    def test_h3_resolution_from_env(self):
        """Test H3 resolution from environment variable."""
        with tempfile.NamedTemporaryFile() as tmp:
            os.environ['H3_RESOLUTION'] = '12'
            config = Config()
            assert config.h3_resolution == 12
            del os.environ['H3_RESOLUTION']

    def test_max_download_retries_default(self):
        """Test default maximum download retries."""
        config = Config()
        assert config.max_download_retries == 3

    def test_max_download_retries_from_env(self):
        """Test maximum download retries from environment variable."""
        with tempfile.NamedTemporaryFile() as tmp:
            os.environ['MAX_DOWNLOAD_RETRIES'] = '5'
            config = Config()
            assert config.max_download_retries == 5
            del os.environ['MAX_DOWNLOAD_RETRIES']

    def test_request_timeout_default(self):
        """Test default request timeout."""
        config = Config()
        assert config.request_timeout == 30

    def test_request_timeout_from_env(self):
        """Test request timeout from environment variable."""
        with tempfile.NamedTemporaryFile() as tmp:
            os.environ['REQUEST_TIMEOUT'] = '60'
            config = Config()
            assert config.request_timeout == 60
            del os.environ['REQUEST_TIMEOUT']

    def test_data_sources_configuration(self):
        """Test that data sources are properly configured."""
        config = Config()
        assert 'earthquakes' in config.data_sources
        assert 'us_states' in config.data_sources
        assert 'world_cities' in config.data_sources

        # Test structure of data source configuration
        population_config = config.data_sources['earthquakes']
        assert 'url' in population_config
        assert 'format' in population_config
        assert 'description' in population_config

    def test_cache_path_generation(self):
        """Test cache path generation for data sources."""
        config = Config()
        cache_path = config.get_cache_path('population')
        assert 'population_processed.h3' in str(cache_path)
        assert cache_path.parent == config.cache_dir

    def test_raw_data_path_generation(self):
        """Test raw data path generation for data sources."""
        config = Config()
        raw_path = config.get_raw_data_path('population', 'geojson')
        assert 'population.geojson' in str(raw_path)
        assert raw_path.parent == config.raw_data_dir

    def test_processed_data_path_generation(self):
        """Test processed data path generation for data sources."""
        config = Config()
        processed_path = config.get_processed_data_path('population')
        assert 'population_processed.h3' in str(processed_path)
        assert processed_path.parent == config.processed_data_dir
