#!/usr/bin/env python3
"""Debug script to examine dashboard HTML response."""

import sys
import time
import threading
import requests
sys.path.insert(0, 'src')

from src.visualization.dashboard import CascadiaDashboard

def debug_dashboard_response():
    """Debug the dashboard response to see what's being rendered."""
    print("🔍 Debugging dashboard response...")

    # Create dashboard instance
    dashboard = CascadiaDashboard()

    # Start dashboard in a separate thread
    def run_dashboard():
        dashboard.run(host='127.0.0.1', port=8052, debug=False)

    server_thread = threading.Thread(target=run_dashboard, daemon=True)
    server_thread.start()

    # Give the server time to start
    print("⏳ Waiting for dashboard server to start...")
    time.sleep(3)

    try:
        # Get the dashboard response
        response = requests.get('http://127.0.0.1:8052', timeout=10)

        print(f"Response status: {response.status_code}")
        print(f"Response length: {len(response.text)} characters")

        # Check for key content
        checks = [
            'Cascadia',
            'Layer Controls',
            'Layer Information',
            'main-map',
            'earthquakes',
            'intensity'
        ]

        print("\n📋 Content checks:")
        for check in checks:
            found = check.lower() in response.text.lower()
            status = "✅" if found else "❌"
            print(f"  {status} '{check}'")

        # Show first 1000 characters of response
        print("\n📄 First 1000 characters of response:")
        print("-" * 50)
        print(response.text[:1000])
        print("-" * 50)

        # Look for layer-related content
        if 'layer' in response.text.lower():
            print("\n🎯 Layer-related content found in response:")
            # Find all occurrences of 'layer' (case insensitive)
            import re
            layer_matches = re.findall(r'.{50}layer.{50}', response.text, re.IGNORECASE)
            for match in layer_matches[:5]:  # Show first 5 matches
                print(f"  ...{match}...")
        else:
            print("\n❌ No layer-related content found")

        return True

    except Exception as e:
        print(f"❌ Error debugging dashboard: {e}")
        return False

if __name__ == "__main__":
    debug_dashboard_response()
