#!/usr/bin/env python3
"""Test script to verify complete dashboard functionality."""

import sys
import os
import time
import threading
import requests
sys.path.insert(0, 'src')

from src.visualization.dashboard import CascadiaDashboard

def test_dashboard_server():
    """Test the complete dashboard server functionality."""
    print("🚀 Testing complete dashboard server functionality...")

    # Create dashboard instance
    dashboard = CascadiaDashboard()
    print("✅ Dashboard instance created")

    # Test layer discovery
    available_layers = dashboard.get_available_layers()
    print(f"📊 Available layers: {available_layers}")

    if not available_layers:
        print("❌ No layers available for dashboard")
        return False

    # Start dashboard in a separate thread
    def run_dashboard():
        dashboard.run(host='127.0.0.1', port=8051, debug=False)

    server_thread = threading.Thread(target=run_dashboard, daemon=True)
    server_thread.start()

    # Give the server time to start
    print("⏳ Waiting for dashboard server to start...")
    time.sleep(3)

    try:
        # Test if server is responding
        response = requests.get('http://127.0.0.1:8051', timeout=10)
        if response.status_code == 200:
            print("✅ Dashboard server is responding (HTTP 200)")
        else:
            print(f"❌ Dashboard server returned HTTP {response.status_code}")
            return False

        # Test if the response contains expected elements
        if 'Cascadia' in response.text:
            print("✅ Dashboard page contains expected content")
        else:
            print("❌ Dashboard page missing expected content")
            return False

        # Test if layer toggles are present in the HTML
        layer_count = 0
        for layer in available_layers:
            if layer.replace('_', ' ').title() in response.text:
                layer_count += 1

        if layer_count > 0:
            print(f"✅ Found {layer_count} layer toggles in dashboard")
        else:
            print("❌ No layer toggles found in dashboard")
            return False

        print("🎉 Dashboard server test completed successfully!")
        return True

    except requests.exceptions.RequestException as e:
        print(f"❌ Could not connect to dashboard server: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error testing dashboard: {e}")
        return False

def test_dashboard_components():
    """Test individual dashboard components without starting server."""
    print("\n🔧 Testing dashboard components...")

    dashboard = CascadiaDashboard()

    # Test empty map creation
    empty_fig = dashboard.create_empty_map()
    if empty_fig:
        print("✅ Empty map creation works")
    else:
        print("❌ Empty map creation failed")
        return False

    # Test layer data loading (simulate callback)
    from src.utils.config import config
    import geopandas as gpd

    layers_dir = config.processed_data_dir / "layers"
    layer_files = list(layers_dir.glob("*_layer.geojson"))

    if not layer_files:
        print("❌ No layer files found for component testing")
        return False

    # Load layer data like the callback does
    layer_data = {}
    for layer_file in layer_files:
        layer_name = layer_file.stem.replace('_layer', '')
        gdf = gpd.read_file(layer_file)
        layer_data[layer_name] = gdf.to_json()

    # Test map figure creation with real data
    fig = dashboard.create_map_figure(layer_data, list(layer_data.keys()))
    if fig and hasattr(fig, 'data') and len(fig.data) > 0:
        print(f"✅ Map figure with {len(fig.data)} layers created successfully")
    else:
        print("❌ Map figure creation failed")
        return False

    return True

if __name__ == "__main__":
    success1 = test_dashboard_components()
    success2 = test_dashboard_server()

    if success1 and success2:
        print("\n✅ All dashboard tests passed!")
        print("📋 Summary:")
        print("  • Dashboard components work correctly")
        print("  • Dashboard server starts and responds")
        print("  • Layer data is loaded and processed")
        print("  • Map visualization is created")
        print("  • UI contains expected elements")
    else:
        print("\n❌ Some dashboard tests failed!")
        if not success1:
            print("  • Component tests failed")
        if not success2:
            print("  • Server tests failed")
        sys.exit(1)
