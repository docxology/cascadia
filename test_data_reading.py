#!/usr/bin/env python3
"""Test script to verify data reading functionality."""

import sys
import os
sys.path.insert(0, 'src')

from src.visualization.dashboard import CascadiaDashboard
from src.utils.config import config
from pathlib import Path
import geopandas as gpd

def test_data_reading():
    """Test if dashboard can read the existing data layers."""
    print("🔍 Testing data reading functionality...")

    # Check if layers directory exists
    layers_dir = config.processed_data_dir / "layers"
    print(f"Layers directory: {layers_dir}")
    print(f"Layers directory exists: {layers_dir.exists()}")

    if not layers_dir.exists():
        print("❌ Layers directory does not exist!")
        return False

    # List all layer files
    layer_files = list(layers_dir.glob("*_layer.geojson"))
    print(f"Found {len(layer_files)} layer files:")
    for f in layer_files:
        print(f"  - {f.name}")

    if not layer_files:
        print("❌ No layer files found!")
        return False

    # Test reading each layer file
    for layer_file in layer_files:
        print(f"\n📂 Testing {layer_file.name}...")
        try:
            gdf = gpd.read_file(layer_file)
            print(f"  ✅ Successfully loaded {len(gdf)} features")

            # Check for required columns
            if 'h3_index' in gdf.columns:
                print("  ✅ H3 index column found")
            else:
                print("  ❌ H3 index column missing")
                return False

            # Check for value column
            value_columns = [col for col in gdf.columns if col not in ['h3_index', 'geometry']]
            if value_columns:
                print(f"  ✅ Value columns found: {value_columns}")
            else:
                print("  ❌ No value columns found")
                return False

            # Check if geometry is valid
            if gdf.geometry.notnull().all():
                print("  ✅ All geometries are valid")
            else:
                print("  ❌ Some geometries are null")
                return False

        except Exception as e:
            print(f"  ❌ Error reading {layer_file.name}: {e}")
            return False

    # Test dashboard layer detection
    print("\n🎛️  Testing dashboard layer detection...")
    dashboard = CascadiaDashboard()
    available_layers = dashboard.get_available_layers()
    print(f"Dashboard found {len(available_layers)} available layers:")
    for layer in available_layers:
        print(f"  - {layer}")

    if not available_layers:
        print("❌ Dashboard found no available layers!")
        return False

    return True

if __name__ == "__main__":
    success = test_data_reading()
    if success:
        print("\n✅ All data reading tests passed!")
    else:
        print("\n❌ Some data reading tests failed!")
        sys.exit(1)
