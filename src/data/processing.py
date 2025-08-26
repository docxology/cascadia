"""Data processing module for cleaning, transforming, and H3-indexing geospatial data."""

import geopandas as gpd
import pandas as pd
from pathlib import Path
from typing import Optional, Dict, Any, List
import json
import logging

from ..utils.config import config
from ..utils.h3_utils import H3Processor

logger = logging.getLogger(__name__)

class DataProcessor:
    """Processes geospatial data with H3 integration and caching."""

    def __init__(self):
        self.h3_processor = H3Processor()

    def load_geospatial_data(self, file_path: Path) -> Optional[gpd.GeoDataFrame]:
        """Load geospatial data from various formats."""
        if not file_path.exists():
            logger.error(f"File does not exist: {file_path}")
            return None

        try:
            if file_path.suffix.lower() == '.geojson':
                gdf = gpd.read_file(file_path)
            elif file_path.suffix.lower() == '.json':
                # Assume GeoJSON format
                gdf = gpd.read_file(file_path)
            elif file_path.suffix.lower() in ['.shp', '.gpkg']:
                gdf = gpd.read_file(file_path)
            elif file_path.suffix.lower() == '.csv':
                # Handle CSV files with coordinate data
                gdf = self._convert_csv_to_geodataframe(file_path)
            else:
                logger.error(f"Unsupported file format: {file_path.suffix}")
                return None

            logger.info(f"Loaded {len(gdf)} features from {file_path}")
            return gdf

        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return None

    def _convert_csv_to_geodataframe(self, file_path: Path) -> gpd.GeoDataFrame:
        """Convert CSV with coordinate data to GeoDataFrame."""
        source_name = file_path.stem
        source_config = config.data_sources.get(source_name, {})

        if not source_config.get('has_coordinates', False):
            raise ValueError(f"Data source {source_name} does not have coordinate information")

        # Read CSV file
        df = pd.read_csv(file_path)

        lat_col = source_config.get('lat_column', 'latitude')
        lon_col = source_config.get('lon_column', 'longitude')
        value_col = source_config.get('value_column')

        if lat_col not in df.columns or lon_col not in df.columns:
            raise ValueError(f"Required coordinate columns {lat_col}, {lon_col} not found")

        # Create geometry from coordinates
        from shapely.geometry import Point
        df['geometry'] = df.apply(lambda row: Point(row[lon_col], row[lat_col]), axis=1)

        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame(df, geometry='geometry')
        gdf = gdf.set_crs('EPSG:4326')

        return gdf

    def clean_geospatial_data(self, gdf: gpd.GeoDataFrame, source_name: str = None) -> gpd.GeoDataFrame:
        """Clean and standardize geospatial data."""
        original_count = len(gdf)

        # Remove rows with invalid geometries
        gdf = gdf[gdf.geometry.notnull()]

        # Ensure consistent coordinate reference system
        if gdf.crs is None:
            # Assume WGS84 if no CRS specified
            gdf = gdf.set_crs('EPSG:4326')
        else:
            # Convert to WGS84 for consistency
            gdf = gdf.to_crs('EPSG:4326')

        # Remove duplicate geometries
        gdf = gdf.drop_duplicates(subset=['geometry'])

        # Source-specific cleaning
        if source_name:
            gdf = self._source_specific_cleaning(gdf, source_name)

        # Reset index
        gdf = gdf.reset_index(drop=True)

        logger.info(f"Cleaned data: {original_count} -> {len(gdf)} features remaining")
        return gdf

    def _source_specific_cleaning(self, gdf: gpd.GeoDataFrame, source_name: str) -> gpd.GeoDataFrame:
        """Apply source-specific data cleaning."""
        if source_name == 'world_cities':
            # Clean world cities data
            # Remove cities with missing population data
            if 'population' in gdf.columns:
                gdf = gdf[gdf['population'].notnull()]
                gdf = gdf[gdf['population'] > 0]

            # Remove cities with invalid coordinates
            gdf = gdf[
                (gdf['lat'].between(-90, 90)) &
                (gdf['lng'].between(-180, 180))
            ]

        elif source_name == 'earthquakes':
            # Clean earthquake data
            # Remove earthquakes with missing magnitude
            if 'mag' in gdf.columns:
                gdf = gdf[gdf['mag'].notnull()]
                gdf = gdf[gdf['mag'] >= 0]

        elif source_name == 'us_states':
            # Clean US states data
            # Add population density if not present (placeholder)
            if 'density' not in gdf.columns:
                # Use area as proxy for density calculation
                gdf['area'] = gdf.geometry.area
                gdf['density'] = 1000 / (gdf['area'] + 1)  # Placeholder calculation

        return gdf

    def process_data_source(self, data_source_name: str,
                           value_column: Optional[str] = None,
                           aggregation_func: str = 'sum',
                           force_reprocess: bool = False) -> Optional[pd.DataFrame]:
        """Process a data source with H3 integration."""
        cache_path = config.get_cache_path(data_source_name)
        processed_path = config.get_processed_data_path(data_source_name)

        # Check cache and skip if exists and not forcing reprocess
        if cache_path.exists() and processed_path.exists() and not force_reprocess:
            logger.info(f"Processed data exists for {data_source_name}, loading from cache")
            return self.load_processed_data(processed_path)

        # Load raw data
        raw_path = config.get_raw_data_path(
            data_source_name,
            config.data_sources[data_source_name]['format']
        )

        gdf = self.load_geospatial_data(raw_path)
        if gdf is None:
            return None

        # Clean data
        gdf = self.clean_geospatial_data(gdf, data_source_name)

        # Determine value column if not specified
        if value_column is None:
            source_config = config.data_sources.get(data_source_name, {})
            value_column = source_config.get('value_column')

        if value_column is None:
            # Use first numeric column as default
            numeric_columns = gdf.select_dtypes(include=['number']).columns
            if len(numeric_columns) > 0:
                value_column = numeric_columns[0]
            else:
                logger.error(f"No numeric columns found in {data_source_name}")
                return None

        if value_column not in gdf.columns:
            logger.error(f"Value column '{value_column}' not found in {data_source_name}")
            return None

        # Process based on geometry type
        if gdf.geometry.iloc[0].geom_type == 'Point':
            result_df = self.h3_processor.aggregate_points_to_h3(
                gdf, value_column, aggregation_func
            )
        else:
            result_df = self.h3_processor.aggregate_polygons_to_h3(
                gdf, value_column, aggregation_func
            )

        # Save processed data
        self.save_processed_data(result_df, processed_path)

        # Update cache
        self.update_cache(data_source_name, cache_path)

        logger.info(f"Processed {data_source_name}: {len(result_df)} H3 cells")
        return result_df

    def save_processed_data(self, df: pd.DataFrame, file_path: Path) -> bool:
        """Save processed H3 data to file."""
        try:
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Save as CSV for H3 data
            df.to_csv(file_path, index=False)
            return True

        except Exception as e:
            logger.error(f"Failed to save processed data to {file_path}: {e}")
            return False

    def load_processed_data(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Load processed H3 data from file."""
        try:
            df = pd.read_csv(file_path)
            return df

        except Exception as e:
            logger.error(f"Failed to load processed data from {file_path}: {e}")
            return None

    def update_cache(self, data_source_name: str, cache_path: Path) -> bool:
        """Update cache file with processing metadata."""
        try:
            cache_info = {
                'data_source': data_source_name,
                'last_processed': pd.Timestamp.now().isoformat(),
                'h3_resolution': self.h3_processor.resolution,
                'config': config.data_sources.get(data_source_name, {})
            }

            with open(cache_path, 'w') as f:
                json.dump(cache_info, f, indent=2)

            return True

        except Exception as e:
            logger.error(f"Failed to update cache for {data_source_name}: {e}")
            return False

    def get_cache_info(self, data_source_name: str) -> Optional[Dict[str, Any]]:
        """Get cache information for a data source."""
        cache_path = config.get_cache_path(data_source_name)

        if not cache_path.exists():
            return None

        try:
            with open(cache_path, 'r') as f:
                return json.load(f)

        except Exception as e:
            logger.error(f"Failed to read cache for {data_source_name}: {e}")
            return None

    def process_all_sources(self, force_reprocess: bool = False) -> Dict[str, Optional[pd.DataFrame]]:
        """Process all configured data sources."""
        results = {}

        for source_name in config.data_sources.keys():
            df = self.process_data_source(source_name, force_reprocess=force_reprocess)
            results[source_name] = df

        return results
