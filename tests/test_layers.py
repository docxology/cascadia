"""Tests for the layer management module."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon

from src.visualization.layers import LayerManager
from src.utils.config import config

class TestLayerManager:
    """Test cases for the LayerManager class."""

    def test_layer_manager_initialization(self):
        """Test LayerManager initialization."""
        manager = LayerManager()
        assert manager.active_layers == set()
        assert manager.layer_metadata == {}
        assert manager.layers_dir == config.processed_data_dir / "layers"

    def test_discover_layers_empty(self):
        """Test discovering layers when none exist."""
        manager = LayerManager()

        with tempfile.TemporaryDirectory() as tmp_dir:
            with patch.object(manager, 'layers_dir', Path(tmp_dir)):
                layers = manager.discover_layers()
                assert layers == []

    def test_discover_layers_with_files(self):
        """Test discovering layers with existing files."""
        manager = LayerManager()

        with tempfile.TemporaryDirectory() as tmp_dir:
            layers_dir = Path(tmp_dir)
            layers_dir.mkdir(exist_ok=True)

            # Create test layer files
            test_data = {
                'h3_index': ['8928308280fffff'],
                'value': [100],
                'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
            }
            gdf = gpd.GeoDataFrame(test_data)

            layer1_path = layers_dir / "population_layer.geojson"
            layer2_path = layers_dir / "infrastructure_layer.geojson"
            gdf.to_file(layer1_path, driver='GeoJSON')
            gdf.to_file(layer2_path, driver='GeoJSON')

            with patch.object(manager, 'layers_dir', layers_dir):
                layers = manager.discover_layers()

                assert len(layers) == 2
                assert 'population' in layers
                assert 'infrastructure' in layers

                # Check that metadata was loaded
                assert 'population' in manager.layer_metadata
                assert 'infrastructure' in manager.layer_metadata

    def test_load_layer_metadata(self):
        """Test loading layer metadata."""
        manager = LayerManager()

        # Create test layer file
        test_data = {
            'h3_index': ['8928308280fffff'],
            'value': [100],
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
        }
        gdf = gpd.GeoDataFrame(test_data)

        with tempfile.NamedTemporaryFile(suffix='_layer.geojson', delete=False) as tmp:
            gdf.to_file(tmp.name, driver='GeoJSON')
            tmp_path = Path(tmp.name)

        try:
            with patch.object(manager, 'layers_dir', tmp_path.parent):
                result = manager.load_layer_metadata('test_layer', tmp_path)

                assert result is None  # Method doesn't return anything on success
                assert 'test_layer' in manager.layer_metadata

                metadata = manager.layer_metadata['test_layer']
                assert metadata['feature_count'] == 1
                assert 'value_range' in metadata
                assert metadata['value_range']['min'] == 100
                assert metadata['value_range']['max'] == 100

        finally:
            tmp_path.unlink()

    def test_activate_layer(self):
        """Test activating a layer."""
        manager = LayerManager()

        # Mock layer metadata
        manager.layer_metadata['test_layer'] = {
            'file_path': Path('/path/to/layer.geojson'),
            'feature_count': 10
        }

        with patch.object(manager, 'get_layer_data') as mock_get_data:
            mock_get_data.return_value = gpd.GeoDataFrame()

            result = manager.activate_layer('test_layer')

            assert result is True
            assert 'test_layer' in manager.active_layers

    def test_activate_layer_no_metadata(self):
        """Test activating a layer without metadata."""
        manager = LayerManager()

        result = manager.activate_layer('nonexistent_layer')
        assert result is False

    def test_deactivate_layer(self):
        """Test deactivating a layer."""
        manager = LayerManager()

        # Activate layer first
        manager.active_layers.add('test_layer')

        result = manager.deactivate_layer('test_layer')

        assert result is True
        assert 'test_layer' not in manager.active_layers

    def test_deactivate_layer_not_active(self):
        """Test deactivating a layer that is not active."""
        manager = LayerManager()

        result = manager.deactivate_layer('nonexistent_layer')
        assert result is False

    def test_toggle_layer(self):
        """Test toggling layer state."""
        manager = LayerManager()

        # Mock layer metadata
        manager.layer_metadata['test_layer'] = {
            'file_path': Path('/path/to/layer.geojson'),
            'feature_count': 10
        }

        with patch.object(manager, 'get_layer_data') as mock_get_data:
            mock_get_data.return_value = gpd.GeoDataFrame()

            # First toggle should activate
            result1 = manager.toggle_layer('test_layer')
            assert result1 is True
            assert 'test_layer' in manager.active_layers

            # Second toggle should deactivate
            result2 = manager.toggle_layer('test_layer')
            assert result2 is True
            assert 'test_layer' not in manager.active_layers

    def test_get_active_layers(self):
        """Test getting list of active layers."""
        manager = LayerManager()

        manager.active_layers = {'layer1', 'layer2', 'layer3'}

        active_layers = manager.get_active_layers()

        assert len(active_layers) == 3
        assert 'layer1' in active_layers
        assert 'layer2' in active_layers
        assert 'layer3' in active_layers

    def test_get_layer_data(self):
        """Test getting layer data."""
        manager = LayerManager()

        # Create test layer file
        test_data = {
            'h3_index': ['8928308280fffff'],
            'value': [100],
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
        }
        gdf = gpd.GeoDataFrame(test_data)

        with tempfile.NamedTemporaryFile(suffix='_layer.geojson', delete=False) as tmp:
            gdf.to_file(tmp.name, driver='GeoJSON')
            tmp_path = Path(tmp.name)

        try:
            manager.layer_metadata['test_layer'] = {'file_path': tmp_path}

            result_gdf = manager.get_layer_data('test_layer')

            assert result_gdf is not None
            assert len(result_gdf) == 1
            assert result_gdf.iloc[0]['value'] == 100

        finally:
            tmp_path.unlink()

    def test_get_layer_data_no_metadata(self):
        """Test getting layer data without metadata."""
        manager = LayerManager()

        result = manager.get_layer_data('nonexistent_layer')
        assert result is None

    def test_get_combined_layer_data(self):
        """Test getting combined data for active layers."""
        manager = LayerManager()

        # Create test data for two layers
        test_data1 = {
            'h3_index': ['8928308280fffff'],
            'value': [100],
            'layer': ['population'],
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
        }

        test_data2 = {
            'h3_index': ['8928308281fffff'],
            'value': [200],
            'layer': ['infrastructure'],
            'geometry': [Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])]
        }

        gdf1 = gpd.GeoDataFrame(test_data1)
        gdf2 = gpd.GeoDataFrame(test_data2)

        manager.active_layers = {'population', 'infrastructure'}
        manager.layer_metadata = {
            'population': {'file_path': Path('/path/to/population_layer.geojson')},
            'infrastructure': {'file_path': Path('/path/to/infrastructure_layer.geojson')}
        }

        with patch.object(manager, 'get_layer_data', side_effect=[gdf1, gdf2]):
            combined_gdf = manager.get_combined_layer_data()

            assert combined_gdf is not None
            assert len(combined_gdf) == 2
            assert 'population' in combined_gdf['layer'].values
            assert 'infrastructure' in combined_gdf['layer'].values

    def test_get_combined_layer_data_no_active_layers(self):
        """Test getting combined data with no active layers."""
        manager = LayerManager()

        combined_gdf = manager.get_combined_layer_data()
        assert combined_gdf is None

    def test_create_layer_composition(self):
        """Test creating layer composition configuration."""
        manager = LayerManager()

        manager.active_layers = {'population', 'infrastructure'}

        layer_configs = {
            'population': {'opacity': 0.8, 'color': 'blue'},
            'infrastructure': {'opacity': 0.6, 'color': 'red'}
        }

        composition = manager.create_layer_composition(layer_configs)

        assert isinstance(composition, str)

        # Parse JSON to verify structure
        comp_dict = json.loads(composition)
        assert 'active_layers' in comp_dict
        assert 'layer_configs' in comp_dict
        assert 'timestamp' in comp_dict
        assert len(comp_dict['active_layers']) == 2

    def test_save_and_load_layer_state(self):
        """Test saving and loading layer state."""
        manager = LayerManager()

        manager.active_layers = {'population', 'infrastructure'}
        manager.layer_metadata = {
            'population': {'feature_count': 100},
            'infrastructure': {'feature_count': 200}
        }

        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)

        try:
            # Save state
            save_result = manager.save_layer_state(tmp_path)
            assert save_result is True

            # Create new manager and load state
            new_manager = LayerManager()
            load_result = new_manager.load_layer_state(tmp_path)

            assert load_result is True
            assert new_manager.active_layers == manager.active_layers
            assert len(new_manager.layer_metadata) == 2

        finally:
            tmp_path.unlink()

    def test_get_layer_statistics(self):
        """Test getting layer statistics."""
        manager = LayerManager()

        manager.active_layers = {'population'}
        manager.layer_metadata = {
            'population': {
                'feature_count': 100,
                'value_range': {'min': 10, 'max': 100, 'mean': 55}
            },
            'infrastructure': {
                'feature_count': 200,
                'value_range': {'min': 5, 'max': 50, 'mean': 25}
            }
        }

        stats = manager.get_layer_statistics()

        assert stats['total_layers'] == 2
        assert stats['active_layers'] == 1
        assert 'population' in stats['layer_details']
        assert 'infrastructure' in stats['layer_details']
        assert stats['layer_details']['population']['is_active'] is True
        assert stats['layer_details']['infrastructure']['is_active'] is False

    def test_validate_layer_data_valid(self):
        """Test validating valid layer data."""
        manager = LayerManager()

        # Create valid test layer
        test_data = {
            'h3_index': ['8928308280fffff'],
            'value': [100],
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
        }
        gdf = gpd.GeoDataFrame(test_data)

        with tempfile.NamedTemporaryFile(suffix='_layer.geojson', delete=False) as tmp:
            gdf.to_file(tmp.name, driver='GeoJSON')
            tmp_path = Path(tmp.name)

        try:
            manager.layer_metadata['test_layer'] = {'file_path': tmp_path}

            validation = manager.validate_layer_data('test_layer')

            assert validation['layer_name'] == 'test_layer'
            assert validation['is_valid'] is True
            assert len(validation['issues']) == 0

        finally:
            tmp_path.unlink()

    def test_validate_layer_data_missing_file(self):
        """Test validating layer data with missing file."""
        manager = LayerManager()

        manager.layer_metadata['test_layer'] = {'file_path': Path('/nonexistent/file.geojson')}

        validation = manager.validate_layer_data('test_layer')

        assert validation['layer_name'] == 'test_layer'
        assert validation['is_valid'] is False
        assert len(validation['issues']) == 1
        assert 'does not exist' in validation['issues'][0]

    def test_validate_layer_data_missing_columns(self):
        """Test validating layer data with missing required columns."""
        manager = LayerManager()

        # Create layer missing required columns
        test_data = {
            'some_other_column': ['data'],
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
        }
        gdf = gpd.GeoDataFrame(test_data)

        with tempfile.NamedTemporaryFile(suffix='_layer.geojson', delete=False) as tmp:
            gdf.to_file(tmp.name, driver='GeoJSON')
            tmp_path = Path(tmp.name)

        try:
            manager.layer_metadata['test_layer'] = {'file_path': tmp_path}

            validation = manager.validate_layer_data('test_layer')

            assert validation['is_valid'] is False
            assert any('Missing required columns' in issue for issue in validation['issues'])

        finally:
            tmp_path.unlink()
