"""Tests for the H3 utilities module."""

import pytest
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
import h3

from src.utils.h3_utils import H3Processor

class TestH3Processor:
    """Test cases for the H3Processor class."""

    def test_h3_processor_initialization(self):
        """Test H3Processor initialization with default resolution."""
        processor = H3Processor()
        assert processor.resolution == 9

    def test_h3_processor_custom_resolution(self):
        """Test H3Processor initialization with custom resolution."""
        processor = H3Processor(resolution=12)
        assert processor.resolution == 12

    def test_point_to_h3_conversion(self):
        """Test conversion of latitude/longitude to H3 index."""
        processor = H3Processor()

        # Test with known coordinates
        lat, lng = 37.7749, -122.4194  # San Francisco
        h3_index = processor.point_to_h3(lat, lng)

        assert isinstance(h3_index, str)
        assert len(h3_index) == 15  # H3 index length at resolution 9
        assert h3.is_valid_cell(h3_index)

    def test_h3_to_geometry_conversion(self):
        """Test conversion of H3 index to polygon geometry."""
        processor = H3Processor()

        # Create a test H3 index
        lat, lng = 37.7749, -122.4194
        h3_index = processor.point_to_h3(lat, lng)

        geometry = processor.h3_to_geometry(h3_index)

        assert isinstance(geometry, Polygon)
        assert geometry.is_valid

    def test_aggregate_points_to_h3_sum(self):
        """Test aggregation of point data to H3 with sum function."""
        processor = H3Processor()

        # Create test GeoDataFrame with points
        points_data = {
            'value': [10, 20, 15, 25],
            'geometry': [
                Point(-122.4194, 37.7749),
                Point(-122.4195, 37.7750),
                Point(-122.4196, 37.7751),
                Point(-122.4197, 37.7752)
            ]
        }
        gdf = gpd.GeoDataFrame(points_data)

        # Aggregate to H3
        result_df = processor.aggregate_points_to_h3(gdf, 'value', 'sum')

        assert len(result_df) > 0
        assert 'h3_index' in result_df.columns
        assert 'value' in result_df.columns
        assert result_df['value'].sum() == 70  # Sum of all values

    def test_aggregate_points_to_h3_mean(self):
        """Test aggregation of point data to H3 with mean function."""
        processor = H3Processor()

        # Create test GeoDataFrame with points in same H3 cell
        lat, lng = 37.7749, -122.4194
        points_data = {
            'value': [10, 20, 30],
            'geometry': [
                Point(lng, lat),
                Point(lng + 0.00001, lat + 0.00001),  # Much closer points
                Point(lng + 0.00002, lat + 0.00002)
            ]
        }
        gdf = gpd.GeoDataFrame(points_data)

        # Aggregate to H3
        result_df = processor.aggregate_points_to_h3(gdf, 'value', 'mean')

        assert len(result_df) == 1  # All points in same H3 cell
        assert result_df['value'].iloc[0] == 20.0  # Mean of 10, 20, 30

    def test_aggregate_polygons_to_h3(self):
        """Test aggregation of polygon data to H3."""
        processor = H3Processor()

        # Create test GeoDataFrame with polygons
        polygons_data = {
            'value': [100, 200],
            'geometry': [
                Polygon([(0, 0), (1, 0), (1, 1), (0, 1)]),
                Polygon([(1, 0), (2, 0), (2, 1), (1, 1)])
            ]
        }
        gdf = gpd.GeoDataFrame(polygons_data)

        # Aggregate to H3
        result_df = processor.aggregate_polygons_to_h3(gdf, 'value', 'sum')

        assert len(result_df) > 0
        assert 'h3_index' in result_df.columns
        assert 'value' in result_df.columns

    def test_h3_dataframe_to_geodataframe(self):
        """Test conversion of H3 dataframe to GeoDataFrame."""
        processor = H3Processor()

        # Create test dataframe with H3 indices
        lat, lng = 37.7749, -122.4194
        h3_index = processor.point_to_h3(lat, lng)

        df_data = {
            'h3_index': [h3_index, h3_index],
            'value': [10, 20]
        }
        df = pd.DataFrame(df_data)

        # Convert to GeoDataFrame
        gdf = processor.h3_dataframe_to_geodataframe(df)

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 2
        assert 'geometry' in gdf.columns
        assert all(isinstance(geom, Polygon) for geom in gdf.geometry)

    def test_get_h3_neighbors(self):
        """Test getting neighboring H3 cells."""
        processor = H3Processor()

        # Create a test H3 index
        lat, lng = 37.7749, -122.4194
        h3_index = processor.point_to_h3(lat, lng)

        # Get neighbors
        neighbors = processor.get_h3_neighbors(h3_index, ring_size=1)

        assert isinstance(neighbors, list)
        assert len(neighbors) == 7  # 6 neighbors + center cell for ring size 1
        assert all(h3.is_valid_cell(neighbor) for neighbor in neighbors)

    def test_calculate_h3_distance(self):
        """Test calculating grid distance between H3 indices."""
        processor = H3Processor()

        # Create two H3 indices
        lat1, lng1 = 37.7749, -122.4194
        lat2, lng2 = 37.7849, -122.4294

        h3_index1 = processor.point_to_h3(lat1, lng1)
        h3_index2 = processor.point_to_h3(lat2, lng2)

        # Calculate distance
        distance = processor.calculate_h3_distance(h3_index1, h3_index2)

        assert isinstance(distance, int)
        assert distance >= 0

    def test_get_h3_center(self):
        """Test getting center coordinates of H3 cell."""
        processor = H3Processor()

        # Create a test H3 index
        lat, lng = 37.7749, -122.4194
        h3_index = processor.point_to_h3(lat, lng)

        # Get center
        center_lat, center_lng = processor.get_h3_center(h3_index)

        assert isinstance(center_lat, float)
        assert isinstance(center_lng, float)
        assert -90 <= center_lat <= 90
        assert -180 <= center_lng <= 180

    def test_aggregate_invalid_geometry_type(self):
        """Test handling of invalid geometry types."""
        processor = H3Processor()

        # Create test GeoDataFrame with invalid geometry
        points_data = {
            'value': [10],
            'geometry': [None]  # Invalid geometry
        }
        gdf = gpd.GeoDataFrame(points_data)

        # This should handle the invalid geometry gracefully
        result_df = processor.aggregate_points_to_h3(gdf, 'value', 'sum')

        # Should return empty or filtered result
        assert isinstance(result_df, pd.DataFrame)

    def test_unsupported_aggregation_function(self):
        """Test handling of unsupported aggregation functions."""
        processor = H3Processor()

        points_data = {
            'value': [10, 20],
            'geometry': [Point(0, 0), Point(0.1, 0.1)]
        }
        gdf = gpd.GeoDataFrame(points_data)

        with pytest.raises(ValueError, match="Unsupported aggregation function"):
            processor.aggregate_points_to_h3(gdf, 'value', 'unsupported_func')
