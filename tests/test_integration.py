"""Tests for the data integration module."""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import geopandas as gpd
from shapely.geometry import Polygon

from src.data.integration import DataIntegrator
from src.utils.config import config

class TestDataIntegrator:
    """Test cases for the DataIntegrator class."""

    def test_data_integrator_initialization(self):
        """Test DataIntegrator initialization."""
        integrator = DataIntegrator()
        assert integrator.h3_processor is not None

    def test_load_processed_sources(self):
        """Test loading processed data sources."""
        integrator = DataIntegrator()

        # Create temporary CSV files
        test_data1 = {'h3_index': ['8928308280fffff'], 'value': [100]}
        test_data2 = {'h3_index': ['8928308280fffff'], 'value': [200]}

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test CSV files
            df1_path = Path(tmp_dir) / "source1_processed.h3"
            df2_path = Path(tmp_dir) / "source2_processed.h3"

            pd.DataFrame(test_data1).to_csv(df1_path, index=False)
            pd.DataFrame(test_data2).to_csv(df2_path, index=False)

            with patch('src.data.integration.config') as mock_config:
                mock_config.get_processed_data_path.side_effect = [df1_path, df2_path]

                results = integrator.load_processed_sources(['source1', 'source2'])

                assert len(results) == 2
                assert 'source1' in results
                assert 'source2' in results
                assert len(results['source1']) == 1
                assert len(results['source2']) == 1

    def test_load_processed_sources_missing_file(self):
        """Test loading processed sources with missing file."""
        integrator = DataIntegrator()

        with patch('src.data.integration.config') as mock_config:
            mock_config.get_processed_data_path.return_value = Path("nonexistent_file.csv")

            results = integrator.load_processed_sources(['missing_source'])

            assert len(results) == 0

    def test_merge_h3_data(self):
        """Test merging H3-indexed datasets."""
        integrator = DataIntegrator()

        # Create test dataframes
        df1 = pd.DataFrame({
            'h3_index': ['8928308280fffff', '8928308281fffff'],
            'value': [100, 200]
        })
        df1_renamed = df1.rename(columns={'value': 'source1_value'})

        df2 = pd.DataFrame({
            'h3_index': ['8928308280fffff', '8928308282fffff'],
            'value': [150, 250]
        })
        df2_renamed = df2.rename(columns={'value': 'source2_value'})

        data_frames = {
            'source1': df1_renamed,
            'source2': df2_renamed
        }

        merged_df = integrator.merge_h3_data(data_frames)

        assert len(merged_df) == 3  # Should have 3 unique H3 indices
        assert 'source1_value' in merged_df.columns
        assert 'source2_value' in merged_df.columns
        assert 'h3_index' in merged_df.columns

        # Check that NaN values are filled with 0
        assert not merged_df.isna().any().any()

    def test_merge_h3_data_empty(self):
        """Test merging with empty data."""
        integrator = DataIntegrator()

        merged_df = integrator.merge_h3_data({})
        assert merged_df.empty

    def test_create_composite_metrics(self):
        """Test creating composite metrics."""
        integrator = DataIntegrator()

        # Create test dataframe
        df = pd.DataFrame({
            'h3_index': ['8928308280fffff', '8928308281fffff'],
            'source1_value': [100, 200],
            'source2_value': [150, 250]
        })

        metrics = {
            'total_value': 'source1_value + source2_value',
            'average_value': '(source1_value + source2_value) / 2'
        }

        result_df = integrator.create_composite_metrics(df, metrics)

        assert 'total_value' in result_df.columns
        assert 'average_value' in result_df.columns
        assert result_df['total_value'].iloc[0] == 250  # 100 + 150
        assert result_df['average_value'].iloc[0] == 125.0  # (100 + 150) / 2

    def test_normalize_data_minmax(self):
        """Test data normalization using min-max scaling."""
        integrator = DataIntegrator()

        df = pd.DataFrame({
            'h3_index': ['a', 'b', 'c'],
            'value1': [10, 20, 30],
            'value2': [100, 200, 300]
        })

        normalized_df = integrator.normalize_data(df, ['value1', 'value2'], 'minmax')

        # Check value1 normalization (10, 20, 30) -> (0, 0.5, 1)
        assert normalized_df['value1'].iloc[0] == 0.0
        assert normalized_df['value1'].iloc[1] == 0.5
        assert normalized_df['value1'].iloc[2] == 1.0

        # Check value2 normalization (100, 200, 300) -> (0, 0.5, 1)
        assert normalized_df['value2'].iloc[0] == 0.0
        assert normalized_df['value2'].iloc[1] == 0.5
        assert normalized_df['value2'].iloc[2] == 1.0

    def test_normalize_data_zscore(self):
        """Test data normalization using z-score."""
        integrator = DataIntegrator()

        df = pd.DataFrame({
            'h3_index': ['a', 'b', 'c'],
            'value': [10, 20, 30]  # Mean=20, std=10
        })

        normalized_df = integrator.normalize_data(df, ['value'], 'zscore')

        # Check z-score normalization
        assert abs(normalized_df['value'].iloc[1]) < 0.001  # Mean should be ~0
        assert abs(normalized_df['value'].std() - 1.0) < 0.001  # Std should be ~1

    def test_normalize_data_robust(self):
        """Test data normalization using robust scaling."""
        integrator = DataIntegrator()

        df = pd.DataFrame({
            'h3_index': ['a', 'b', 'c'],
            'value': [10, 20, 30]
        })

        normalized_df = integrator.normalize_data(df, ['value'], 'robust')

        # Check that robust scaling was applied (should not raise error)
        assert 'value' in normalized_df.columns
        assert len(normalized_df) == 3

    def test_create_visualization_dataset(self):
        """Test creating visualization dataset."""
        integrator = DataIntegrator()

        # Create test CSV files
        test_data1 = {'h3_index': ['8928308280fffff'], 'value': [100]}
        test_data2 = {'h3_index': ['8928308280fffff'], 'value': [200]}

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create test files
            df1_path = Path(tmp_dir) / "source1_processed.h3"
            df2_path = Path(tmp_dir) / "source2_processed.h3"

            pd.DataFrame(test_data1).to_csv(df1_path, index=False)
            pd.DataFrame(test_data2).to_csv(df2_path, index=False)

            with patch('src.data.integration.config') as mock_config:
                mock_config.get_processed_data_path.side_effect = [df1_path, df2_path]
                mock_config.processed_data_dir = Path(tmp_dir)

                gdf = integrator.create_visualization_dataset(['source1', 'source2'])

                assert gdf is not None
                assert len(gdf) > 0
                assert 'geometry' in gdf.columns

    def test_create_visualization_dataset_no_sources(self):
        """Test creating visualization dataset with no sources."""
        integrator = DataIntegrator()

        gdf = integrator.create_visualization_dataset([])
        assert gdf is None

    def test_get_data_summary(self):
        """Test generating data summary."""
        integrator = DataIntegrator()

        # Create test GeoDataFrame
        test_data = {
            'h3_index': ['8928308280fffff', '8928308281fffff'],
            'value1': [100, 200],
            'value2': [150, 250],
            'geometry': [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
            ]
        }
        gdf = gpd.GeoDataFrame(test_data)

        summary = integrator.get_data_summary(gdf)

        assert summary['total_h3_cells'] == 2
        assert 'value1' in summary['summary_stats']
        assert 'value2' in summary['summary_stats']
        assert summary['summary_stats']['value1']['mean'] == 150.0
        assert summary['summary_stats']['value1']['min'] == 100
        assert summary['summary_stats']['value1']['max'] == 200

    def test_export_data_layers(self):
        """Test exporting data layers."""
        integrator = DataIntegrator()

        # Create test GeoDataFrame
        test_data = {
            'h3_index': ['8928308280fffff'],
            'layer1_value': [100],
            'layer2_value': [200],
            'geometry': [Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])]
        }
        gdf = gpd.GeoDataFrame(test_data)

        with tempfile.TemporaryDirectory() as tmp_dir:
            output_dir = Path(tmp_dir) / "layers"

            exported_files = integrator.export_data_layers(gdf, output_dir)

            assert len(exported_files) == 2
            assert 'layer1_value' in exported_files
            assert 'layer2_value' in exported_files

            # Check that files were created
            for layer_name, file_path in exported_files.items():
                assert file_path.exists()
                assert file_path.suffix == '.geojson'

                # Verify content
                layer_gdf = gpd.read_file(file_path)
                assert len(layer_gdf) == 1
                assert 'value' in layer_gdf.columns
