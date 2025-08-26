#!/usr/bin/env python3
"""Test script to verify dashboard layer functionality."""

import sys
import os
sys.path.insert(0, 'src')

from src.visualization.dashboard import CascadiaDashboard
from src.utils.config import config
from pathlib import Path
import json

def test_dashboard_layer_loading():
    """Test if dashboard can load and process layers correctly."""
    print("🧪 Testing dashboard layer functionality...")

    # Create dashboard instance
    dashboard = CascadiaDashboard()

    # Test layer discovery
    available_layers = dashboard.get_available_layers()
    print(f"Available layers: {available_layers}")

    if not available_layers:
        print("❌ No layers available")
        return False

    # Test layer toggle creation
    layers_dir = config.processed_data_dir / "layers"
    layer_files = list(layers_dir.glob("*_layer.geojson"))

    print(f"Found {len(layer_files)} layer files:")
    for f in layer_files:
        print(f"  - {f.name}")

    # Test the layer toggle callback logic
    print("\n🧩 Testing layer toggle callback logic...")

    # Simulate the callback that loads layer data
    toggles = []
    layer_data = {}

    for layer_file in layer_files:
        layer_name = layer_file.stem.replace('_layer', '')
        print(f"Processing layer: {layer_name}")

        # Load layer data (simulate what the callback does)
        try:
            import geopandas as gpd
            gdf = gpd.read_file(layer_file)
            layer_data[layer_name] = gdf.to_json()
            print(f"  ✅ Loaded {len(gdf)} features for {layer_name}")

            # Check for required columns
            if 'h3_index' in gdf.columns:
                print("  ✅ H3 index column found")
            else:
                print("  ❌ H3 index column missing")
                return False

            # Check for value columns
            value_columns = [col for col in gdf.columns if col not in ['h3_index', 'geometry']]
            if value_columns:
                print(f"  ✅ Value columns found: {value_columns}")
            else:
                print("  ❌ No value columns found")
                return False

        except Exception as e:
            print(f"  ❌ Error loading {layer_file.name}: {e}")
            return False

    print(f"\n📊 Layer data loaded successfully for {len(layer_data)} layers")

    # Test map figure creation
    print("\n🗺️  Testing map figure creation...")
    try:
        fig = dashboard.create_map_figure(layer_data, list(layer_data.keys()))
        if fig and hasattr(fig, 'data') and fig.data:
            print(f"  ✅ Map figure created with {len(fig.data)} traces")
            for i, trace in enumerate(fig.data):
                trace_name = getattr(trace, 'name', 'Unnamed')
                print(f"    Trace {i}: {trace_name}")
        else:
            print("  ❌ Map figure creation failed")
            return False
    except Exception as e:
        print(f"  ❌ Error creating map figure: {e}")
        return False

    return True

if __name__ == "__main__":
    success = test_dashboard_layer_loading()
    if success:
        print("\n✅ All dashboard layer tests passed!")
    else:
        print("\n❌ Some dashboard layer tests failed!")
        sys.exit(1)
