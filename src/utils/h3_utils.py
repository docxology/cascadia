"""H3 geospatial utilities for Cascadia data integration system."""

import h3
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from typing import List, Dict, Any, Optional, Tuple
import numpy as np

from .config import config

class H3Processor:
    """H3 geospatial indexing processor with data integration capabilities."""

    def __init__(self, resolution: Optional[int] = None):
        self.resolution = resolution or config.h3_resolution

    def point_to_h3(self, lat: float, lng: float) -> str:
        """Convert latitude/longitude point to H3 index."""
        return h3.latlng_to_cell(lat, lng, self.resolution)

    def polygon_to_h3_cells(self, geometry) -> List[str]:
        """Convert polygon geometry to H3 cell indices."""
        if isinstance(geometry, Polygon):
            # Convert shapely polygon to H3 LatLngPoly format
            coords = list(geometry.exterior.coords)
            # Convert (lng, lat) to [(lat, lng), ...] for H3
            h3_coords = [(lat, lng) for lng, lat in coords]
            h3_poly = h3.LatLngPoly(h3_coords)
            cells = h3.polygon_to_cells(h3_poly, self.resolution)
            return cells
        return []

    def h3_to_geometry(self, h3_index: str) -> Polygon:
        """Convert H3 index to polygon geometry."""
        boundary = h3.cell_to_boundary(h3_index)
        # Convert to shapely polygon
        coords = [(lng, lat) for lat, lng in boundary]
        return Polygon(coords)

    def aggregate_points_to_h3(self, gdf: gpd.GeoDataFrame,
                              value_column: str,
                              aggregation_func: str = 'sum') -> pd.DataFrame:
        """Aggregate point data to H3 hexagons."""
        h3_indices = []

        for _, row in gdf.iterrows():
            if isinstance(row.geometry, Point):
                lat, lng = row.geometry.y, row.geometry.x
                h3_index = self.point_to_h3(lat, lng)
                h3_indices.append(h3_index)
            else:
                h3_indices.append(None)

        result_df = pd.DataFrame({
            'h3_index': h3_indices,
            'value': gdf[value_column].values
        })

        # Remove None values
        result_df = result_df.dropna()

        # Aggregate by H3 index
        if aggregation_func == 'sum':
            aggregated = result_df.groupby('h3_index')['value'].sum().reset_index()
        elif aggregation_func == 'mean':
            aggregated = result_df.groupby('h3_index')['value'].mean().reset_index()
        elif aggregation_func == 'count':
            aggregated = result_df.groupby('h3_index')['value'].count().reset_index()
        else:
            raise ValueError(f"Unsupported aggregation function: {aggregation_func}")

        return aggregated

    def aggregate_polygons_to_h3(self, gdf: gpd.GeoDataFrame,
                                value_column: str,
                                aggregation_func: str = 'sum') -> pd.DataFrame:
        """Aggregate polygon data to H3 hexagons."""
        h3_data = []

        for _, row in gdf.iterrows():
            h3_cells = self.polygon_to_h3_cells(row.geometry)
            value = row[value_column]

            for cell in h3_cells:
                h3_data.append({
                    'h3_index': cell,
                    'value': value
                })

        result_df = pd.DataFrame(h3_data)

        # Aggregate by H3 index
        if aggregation_func == 'sum':
            aggregated = result_df.groupby('h3_index')['value'].sum().reset_index()
        elif aggregation_func == 'mean':
            aggregated = result_df.groupby('h3_index')['value'].mean().reset_index()
        elif aggregation_func == 'count':
            aggregated = result_df.groupby('h3_index')['value'].count().reset_index()
        else:
            raise ValueError(f"Unsupported aggregation function: {aggregation_func}")

        return aggregated

    def h3_dataframe_to_geodataframe(self, df: pd.DataFrame) -> gpd.GeoDataFrame:
        """Convert H3 dataframe to GeoDataFrame with geometries."""
        geometries = []

        for _, row in df.iterrows():
            h3_index = row['h3_index']
            geometry = self.h3_to_geometry(h3_index)
            geometries.append(geometry)

        gdf = gpd.GeoDataFrame(df, geometry=geometries)
        return gdf

    def get_h3_neighbors(self, h3_index: str, ring_size: int = 1) -> List[str]:
        """Get neighboring H3 cells within specified ring size."""
        return h3.grid_disk(h3_index, ring_size)

    def calculate_h3_distance(self, h3_index1: str, h3_index2: str) -> int:
        """Calculate grid distance between two H3 indices."""
        return h3.grid_distance(h3_index1, h3_index2)

    def get_h3_center(self, h3_index: str) -> Tuple[float, float]:
        """Get latitude and longitude of H3 cell center."""
        return h3.cell_to_latlng(h3_index)
