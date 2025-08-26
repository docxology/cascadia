"""Data integration module for merging and preparing geospatial data for visualization."""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

from ..utils.config import config
from ..utils.h3_utils import H3Processor

logger = logging.getLogger(__name__)

class DataIntegrator:
    """Integrates multiple data sources into unified datasets for visualization."""

    def __init__(self):
        self.h3_processor = H3Processor()

    def load_processed_sources(self, source_names: List[str]) -> Dict[str, pd.DataFrame]:
        """Load processed data for specified sources."""
        data_frames = {}

        for source_name in source_names:
            processed_path = config.get_processed_data_path(source_name)

            if processed_path.exists():
                df = pd.read_csv(processed_path)
                data_frames[source_name] = df
                logger.info(f"Loaded {len(df)} records for {source_name}")
            else:
                logger.warning(f"Processed data not found for {source_name}")

        return data_frames

    def merge_h3_data(self, data_frames: Dict[str, pd.DataFrame],
                     how: str = 'outer') -> pd.DataFrame:
        """Merge multiple H3-indexed datasets."""
        if not data_frames:
            return pd.DataFrame()

        # Start with the first dataframe
        merged_df = None
        data_sources = list(data_frames.keys())

        for i, source_name in enumerate(data_sources):
            df = data_frames[source_name]
            df_renamed = df.rename(columns={'value': f'{source_name}_value'})

            if i == 0:
                merged_df = df_renamed
            else:
                merged_df = merged_df.merge(
                    df_renamed,
                    on='h3_index',
                    how=how
                )

        # Fill NaN values with 0
        merged_df = merged_df.fillna(0)

        logger.info(f"Merged {len(data_sources)} sources into {len(merged_df)} H3 cells")
        return merged_df

    def create_composite_metrics(self, merged_df: pd.DataFrame,
                                metrics: Dict[str, str]) -> pd.DataFrame:
        """Create composite metrics from merged data."""
        df = merged_df.copy()

        for metric_name, expression in metrics.items():
            try:
                # Evaluate the expression safely
                df[metric_name] = df.eval(expression)
                logger.info(f"Created composite metric: {metric_name}")
            except Exception as e:
                logger.error(f"Failed to create metric {metric_name}: {e}")

        return df

    def normalize_data(self, df: pd.DataFrame,
                      columns: List[str],
                      method: str = 'minmax') -> pd.DataFrame:
        """Normalize specified columns using different methods."""
        df_normalized = df.copy()

        for column in columns:
            if column not in df.columns:
                logger.warning(f"Column {column} not found for normalization")
                continue

            if method == 'minmax':
                min_val = df[column].min()
                max_val = df[column].max()
                if max_val != min_val:
                    df_normalized[column] = (df[column] - min_val) / (max_val - min_val)
            elif method == 'zscore':
                mean_val = df[column].mean()
                std_val = df[column].std()
                if std_val != 0:
                    df_normalized[column] = (df[column] - mean_val) / std_val
            elif method == 'robust':
                median_val = df[column].median()
                mad_val = (df[column] - median_val).abs().median()
                if mad_val != 0:
                    df_normalized[column] = (df[column] - median_val) / mad_val

        return df_normalized

    def create_visualization_dataset(self, source_names: List[str],
                                   composite_metrics: Optional[Dict[str, str]] = None,
                                   normalize_columns: Optional[List[str]] = None) -> Optional[pd.DataFrame]:
        """Create a unified dataset ready for visualization."""
        # Load processed data
        data_frames = self.load_processed_sources(source_names)
        if not data_frames:
            logger.error("No data sources could be loaded")
            return None

        # Merge datasets
        merged_df = self.merge_h3_data(data_frames)

        if merged_df.empty:
            logger.error("Merged dataset is empty")
            return None

        # Add composite metrics if specified
        if composite_metrics:
            merged_df = self.create_composite_metrics(merged_df, composite_metrics)

        # Normalize data if specified
        if normalize_columns:
            merged_df = self.normalize_data(merged_df, normalize_columns)

        # Convert to GeoDataFrame with geometries
        gdf = self.h3_processor.h3_dataframe_to_geodataframe(merged_df)

        # Save integrated dataset
        output_path = config.processed_data_dir / "integrated_dataset.geojson"
        gdf.to_file(output_path, driver='GeoJSON')

        logger.info(f"Created integrated dataset with {len(gdf)} features")
        return gdf

    def get_data_summary(self, integrated_df: pd.DataFrame) -> Dict[str, Any]:
        """Generate summary statistics for integrated data."""
        summary = {
            'total_h3_cells': len(integrated_df),
            'columns': list(integrated_df.columns),
            'data_types': integrated_df.dtypes.to_dict(),
            'summary_stats': {}
        }

        # Generate summary statistics for numeric columns
        numeric_columns = integrated_df.select_dtypes(include=['number']).columns

        for column in numeric_columns:
            summary['summary_stats'][column] = {
                'mean': float(integrated_df[column].mean()),
                'median': float(integrated_df[column].median()),
                'std': float(integrated_df[column].std()),
                'min': float(integrated_df[column].min()),
                'max': float(integrated_df[column].max()),
                'non_zero_count': int((integrated_df[column] != 0).sum())
            }

        return summary

    def export_data_layers(self, integrated_df: pd.DataFrame,
                          output_dir: Optional[Path] = None) -> Dict[str, Path]:
        """Export data as separate layers for visualization."""
        if output_dir is None:
            output_dir = config.processed_data_dir / "layers"

        output_dir.mkdir(parents=True, exist_ok=True)
        exported_files = {}

        # Get all value columns (excluding h3_index and geometry)
        value_columns = [col for col in integrated_df.columns
                        if col not in ['h3_index', 'geometry'] and
                        integrated_df[col].dtype in ['float64', 'int64']]

        for column in value_columns:
            # Create layer with h3_index, geometry, and the specific value
            layer_df = integrated_df[['h3_index', 'geometry', column]].copy()

            # Rename column for consistency
            layer_df = layer_df.rename(columns={column: 'value'})

            # Export as GeoJSON
            output_path = output_dir / f"{column}_layer.geojson"
            layer_gdf = gpd.GeoDataFrame(layer_df, geometry='geometry')
            layer_gdf.to_file(output_path, driver='GeoJSON')

            exported_files[column] = output_path
            logger.info(f"Exported layer: {column}")

        return exported_files
