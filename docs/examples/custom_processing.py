#!/usr/bin/env python3
"""
Custom Data Processing Example

This example shows how to extend Cascadia with custom data processing
logic for specific data sources or analysis requirements.
"""

import sys
from pathlib import Path
import pandas as pd
import geopandas as gpd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.processing import DataProcessor
from data.integration import DataIntegrator
from utils.h3_utils import H3Processor

class CustomDataProcessor(DataProcessor):
    """Extended data processor with custom logic."""

    def process_environmental_data(self, source_name: str) -> pd.DataFrame:
        """Custom processing for environmental data with specialized logic."""
        print(f"Processing environmental data: {source_name}")

        # Load raw data
        raw_path = self.config.get_raw_data_path(source_name, 'geojson')
        gdf = self.load_geospatial_data(raw_path)

        if gdf is None:
            return None

        # Custom environmental data cleaning
        gdf = self.clean_environmental_data(gdf)

        # Custom H3 aggregation with environmental weighting
        h3_df = self.aggregate_environmental_to_h3(gdf, 'environmental_score')

        return h3_df

    def clean_environmental_data(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """Custom cleaning logic for environmental data."""
        # Remove invalid environmental readings
        gdf = gdf[gdf['environmental_score'] >= 0]
        gdf = gdf[gdf['environmental_score'] <= 100]

        # Standardize coordinate reference system
        if gdf.crs is None:
            gdf = gdf.set_crs('EPSG:4326')
        gdf = gdf.to_crs('EPSG:4326')

        # Remove outliers using IQR method
        Q1 = gdf['environmental_score'].quantile(0.25)
        Q3 = gdf['environmental_score'].quantile(0.75)
        IQR = Q3 - Q1
        gdf = gdf[
            (gdf['environmental_score'] >= Q1 - 1.5 * IQR) &
            (gdf['environmental_score'] <= Q3 + 1.5 * IQR)
        ]

        return gdf

    def aggregate_environmental_to_h3(self, gdf: gpd.GeoDataFrame,
                                    value_column: str) -> pd.DataFrame:
        """Custom H3 aggregation for environmental data."""
        # Use higher resolution for environmental data
        original_resolution = self.h3_processor.resolution
        self.h3_processor.resolution = 11  # Higher resolution for precision

        try:
            if gdf.geometry.iloc[0].geom_type == 'Point':
                result_df = self.h3_processor.aggregate_points_to_h3(
                    gdf, value_column, 'mean'  # Use mean for environmental averaging
                )
            else:
                result_df = self.h3_processor.aggregate_polygons_to_h3(
                    gdf, value_column, 'mean'
                )

            return result_df

        finally:
            # Restore original resolution
            self.h3_processor.resolution = original_resolution

class CustomIntegrator(DataIntegrator):
    """Extended integrator with custom analysis methods."""

    def create_environmental_risk_index(self, sources: list) -> gpd.GeoDataFrame:
        """Create a composite environmental risk index."""
        print("Creating environmental risk index...")

        # Load processed environmental data
        env_data = {}
        for source in sources:
            if 'environmental' in source.lower():
                df = self.load_processed_sources([source])
                if df:
                    env_data[source] = df[source]

        if not env_data:
            print("No environmental data found")
            return None

        # Create risk index: weighted combination of environmental factors
        risk_weights = {
            'air_quality': 0.4,
            'water_quality': 0.3,
            'soil_contamination': 0.3
        }

        # Merge environmental datasets
        merged_df = self.merge_h3_data(env_data)

        # Calculate risk index
        risk_expression = ' + '.join([
            f"{weight} * {col}" for col, weight in risk_weights.items()
            if col in merged_df.columns
        ])

        if risk_expression:
            merged_df['environmental_risk_index'] = merged_df.eval(risk_expression)
            merged_df['risk_category'] = pd.cut(
                merged_df['environmental_risk_index'],
                bins=[0, 25, 50, 75, 100],
                labels=['Low', 'Moderate', 'High', 'Critical']
            )

        # Convert to GeoDataFrame
        gdf = self.h3_processor.h3_dataframe_to_geodataframe(merged_df)

        return gdf

    def analyze_spatial_patterns(self, integrated_data: gpd.GeoDataFrame):
        """Analyze spatial patterns in the data."""
        print("Analyzing spatial patterns...")

        analysis_results = {
            'spatial_autocorrelation': {},
            'hotspots': {},
            'clusters': {}
        }

        # Simple spatial analysis: identify high-value clusters
        for column in integrated_data.columns:
            if column not in ['h3_index', 'geometry'] and integrated_data[column].dtype in ['float64', 'int64']:
                values = integrated_data[column]

                # Find top 10% highest values
                threshold = values.quantile(0.9)
                hotspots = integrated_data[values >= threshold]

                analysis_results['hotspots'][column] = {
                    'count': len(hotspots),
                    'percentage': len(hotspots) / len(integrated_data) * 100,
                    'mean_value': hotspots[column].mean()
                }

        return analysis_results

def custom_workflow_example():
    """Demonstrate custom processing workflow."""
    print("🔬 Custom Cascadia Processing Example")
    print("=" * 50)

    # Initialize custom processor
    custom_processor = CustomDataProcessor()

    # Process environmental data with custom logic
    print("\n🌿 Processing environmental data...")
    env_df = custom_processor.process_environmental_data('environmental')

    if env_df is not None:
        print(f"✓ Environmental data processed: {len(env_df)} H3 cells")
        print(f"  Mean environmental score: {env_df['value'].mean():.2f}")
        print(f"  Score range: {env_df['value'].min():.2f} - {env_df['value'].max():.2f}")
    else:
        print("✗ Environmental data processing failed")
        return

    # Custom integration
    print("\n🔗 Custom integration...")
    custom_integrator = CustomIntegrator()

    sources = ['population', 'infrastructure', 'environmental']
    integrated_data = custom_integrator.create_visualization_dataset(sources)

    if integrated_data is not None:
        print(f"✓ Custom integration complete: {len(integrated_data)} features")

        # Create environmental risk index
        risk_data = custom_integrator.create_environmental_risk_index(sources)

        if risk_data is not None:
            print("✓ Environmental risk index created")
            print(f"  Risk categories: {risk_data['risk_category'].value_counts().to_dict()}")

        # Analyze spatial patterns
        patterns = custom_integrator.analyze_spatial_patterns(integrated_data)
        print("\n📊 Spatial Pattern Analysis:")

        for layer, hotspots in patterns['hotspots'].items():
            print(f"  {layer} hotspots:")
            print(f"    Count: {hotspots['count']}")
            print(f"    Percentage: {hotspots['percentage']:.1f}%")
            print(f"    Mean value: {hotspots['mean_value']:.2f}")

    print("\n🎉 Custom processing complete!")

if __name__ == '__main__':
    custom_workflow_example()
