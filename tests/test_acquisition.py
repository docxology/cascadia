"""Tests for the data acquisition module."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.data.acquisition import DataAcquirer
from src.utils.config import config

class TestDataAcquirer:
    """Test cases for the DataAcquirer class."""

    def test_data_acquirer_initialization(self):
        """Test DataAcquirer initialization."""
        acquirer = DataAcquirer()
        assert acquirer.session is not None
        assert acquirer.request_timeout == config.request_timeout > 0

    def test_calculate_file_hash(self):
        """Test file hash calculation."""
        acquirer = DataAcquirer()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("test content for hashing")
            tmp_path = Path(tmp.name)

        try:
            hash_value = acquirer.calculate_file_hash(tmp_path)
            assert isinstance(hash_value, str)
            assert len(hash_value) == 64  # SHA256 hash length
        finally:
            tmp_path.unlink()

    def test_calculate_file_hash_nonexistent(self):
        """Test file hash calculation for nonexistent file."""
        acquirer = DataAcquirer()

        hash_value = acquirer.calculate_file_hash(Path("nonexistent_file.txt"))
        assert hash_value == ""

    @patch('src.data.acquisition.requests.Session.get')
    def test_download_file_success(self, mock_get):
        """Test successful file download."""
        # Mock response
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'test', b' data']
        mock_response.raise_for_status.return_value = None
        mock_response.ok = True
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/plain', 'content-length': '9'}
        mock_get.return_value = mock_response

        acquirer = DataAcquirer()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            success, download_info = acquirer.download_file("http://example.com/test.txt", tmp_path)
            assert success is True
            assert tmp_path.exists()

            # Verify content was written
            with open(tmp_path, 'rb') as f:
                content = f.read()
            assert content == b'test data'

        finally:
            tmp_path.unlink()

    @patch('src.data.acquisition.requests.Session.get')
    def test_download_file_failure(self, mock_get):
        """Test failed file download."""
        # Mock failed response
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Download failed")
        mock_get.return_value = mock_response

        acquirer = DataAcquirer()

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            success, download_info = acquirer.download_file("http://example.com/test.txt", tmp_path)
            assert success is False
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

    def test_acquire_data_source_new_download(self):
        """Test acquiring data source with new download."""
        acquirer = DataAcquirer()

        with patch.object(acquirer, 'download_file', return_value=(True, {})) as mock_download:
            with tempfile.TemporaryDirectory() as tmp_dir:
                # Mock config for testing
                with patch('src.data.acquisition.config') as mock_config:
                    mock_config.data_sources = {
                        'test_source': {
                            'url': 'http://example.com/test.geojson',
                            'format': 'geojson',
                            'description': 'Test data'
                        }
                    }
                    mock_config.get_raw_data_path.return_value = Path(tmp_dir) / "test.geojson"

                    result = acquirer.acquire_data_source('test_source', force_download=True)

                    assert mock_download.called
                    assert result is not None

    def test_acquire_data_source_skip_download(self):
        """Test skipping download when file exists."""
        acquirer = DataAcquirer()

        with patch.object(acquirer, 'download_file') as mock_download:
            with tempfile.NamedTemporaryFile(suffix='.geojson', delete=False) as tmp:
                tmp_path = Path(tmp.name)

            try:
                # Mock config
                with patch('src.data.acquisition.config') as mock_config:
                    mock_config.data_sources = {
                        'test_source': {
                            'url': 'http://example.com/test.geojson',
                            'format': 'geojson'
                        }
                    }
                    mock_config.get_raw_data_path.return_value = tmp_path

                    result = acquirer.acquire_data_source('test_source', force_download=False)

                    # Should not download since file exists
                    assert not mock_download.called
                    assert result == tmp_path

            finally:
                tmp_path.unlink()

    def test_acquire_data_source_unknown(self):
        """Test acquiring unknown data source."""
        acquirer = DataAcquirer()

        with patch('src.data.acquisition.config') as mock_config:
            mock_config.data_sources = {}

            result = acquirer.acquire_data_source('unknown_source')
            assert result is None

    def test_acquire_all_sources(self):
        """Test acquiring all configured data sources."""
        acquirer = DataAcquirer()

        with patch.object(acquirer, 'acquire_data_source') as mock_acquire:
            mock_acquire.return_value = Path("/path/to/file.geojson")

            with patch('src.data.acquisition.config') as mock_config:
                mock_config.data_sources = {
                    'source1': {'url': 'http://example.com/1', 'format': 'geojson'},
                    'source2': {'url': 'http://example.com/2', 'format': 'geojson'}
                }

                results = acquirer.acquire_all_sources()

                assert len(results) == 2
                assert mock_acquire.call_count == 2

    def test_validate_data_integrity_valid(self):
        """Test validating data integrity for valid file."""
        acquirer = DataAcquirer()

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write('{"type": "FeatureCollection", "features": []}')
            tmp_path = Path(tmp.name)

        try:
            result = acquirer.validate_data_integrity(tmp_path)
            assert result is True
        finally:
            tmp_path.unlink()

    def test_validate_data_integrity_nonexistent(self):
        """Test validating data integrity for nonexistent file."""
        acquirer = DataAcquirer()

        result = acquirer.validate_data_integrity(Path("nonexistent_file.txt"))
        assert result is False

    def test_validate_data_integrity_with_expected_hash(self):
        """Test validating data integrity with expected hash."""
        acquirer = DataAcquirer()

        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp:
            tmp.write("test content")
            tmp_path = Path(tmp.name)

        try:
            # Calculate actual hash
            actual_hash = acquirer.calculate_file_hash(tmp_path)

            # Validate with correct hash
            result = acquirer.validate_data_integrity(tmp_path, actual_hash)
            assert result is True

            # Validate with incorrect hash
            result = acquirer.validate_data_integrity(tmp_path, "wrong_hash")
            assert result is False

        finally:
            tmp_path.unlink()

    def test_get_data_info(self):
        """Test getting data information."""
        acquirer = DataAcquirer()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.geojson', delete=False) as tmp:
            tmp.write('{"type": "FeatureCollection", "features": []}')
            tmp_path = Path(tmp.name)

        try:
            with patch('src.data.acquisition.config') as mock_config:
                mock_config.data_sources = {
                    'test_source': {
                        'url': 'http://example.com/test.geojson',
                        'format': 'geojson',
                        'description': 'Test data'
                    }
                }
                mock_config.get_raw_data_path.return_value = tmp_path

                info = acquirer.get_data_info('test_source')

                assert info is not None
                assert info['source_name'] == 'test_source'
                assert info['file_path'] == tmp_path
                assert 'file_size' in info
                assert 'last_modified' in info
                assert 'hash' in info

        finally:
            tmp_path.unlink()

    def test_get_data_info_unknown_source(self):
        """Test getting data information for unknown source."""
        acquirer = DataAcquirer()

        with patch('src.data.acquisition.config') as mock_config:
            mock_config.data_sources = {}

            info = acquirer.get_data_info('unknown_source')
            assert info is None
