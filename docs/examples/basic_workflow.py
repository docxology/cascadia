#!/usr/bin/env python3
"""
Basic Cascadia Workflow Example

This example demonstrates the complete Cascadia workflow:
1. Acquire data from configured sources
2. Process data with H3 integration
3. Integrate multiple data sources
4. Launch interactive dashboard
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from data.acquisition import DataAcquirer
from data.processing import DataProcessor
from data.integration import DataIntegrator
from visualization.dashboard import CascadiaDashboard

def basic_workflow():
    """Execute the basic Cascadia workflow."""

    print("🚀 Starting Cascadia Basic Workflow")
    print("=" * 50)

    # Step 1: Acquire data
    print("\n📥 Step 1: Acquiring data sources...")
    acquirer = DataAcquirer()
    sources = ['earthquakes', 'us_states']

    acquire_results = acquirer.acquire_all_sources(force_download=False)

    for source_name, file_path in acquire_results.items():
        if file_path:
            print(f"   ✓ {source_name}: {file_path}")
        else:
            print(f"   ✗ {source_name}: Failed to acquire")

    # Step 2: Process data
    print("\n⚙️  Step 2: Processing data with H3 integration...")
    processor = DataProcessor()

    for source_name in sources:
        print(f"   Processing {source_name}...")
        df = processor.process_data_source(source_name, force_reprocess=False)

        if df is not None:
            print(f"   ✓ {source_name}: {len(df)} H3 cells created")
        else:
            print(f"   ✗ {source_name}: Processing failed")

    # Step 3: Integrate data
    print("\n🔗 Step 3: Integrating data sources...")
    integrator = DataIntegrator()

    composite_metrics = {
        'combined_score': 'earthquakes_value + us_states_value',
    }

    integrated_data = integrator.create_visualization_dataset(
        sources,
        composite_metrics
    )

    if integrated_data is not None:
        print(f"   ✓ Integration complete: {len(integrated_data)} features")
        print(f"   ✓ Columns: {list(integrated_data.columns)}")
    else:
        print("   ✗ Integration failed")
        return

    # Step 4: Display data summary
    print("\n📊 Step 4: Data summary...")
    summary = integrator.get_data_summary(integrated_data)

    print(f"   Total H3 cells: {summary['total_h3_cells']}")
    print(f"   Available columns: {summary['columns']}")

    for column, stats in summary['summary_stats'].items():
        print(f"   {column}:")
        print(f"     Mean: {stats['mean']:.2f}")
        print(f"     Range: {stats['min']:.2f} - {stats['max']:.2f}")
        print(f"     Non-zero values: {stats['non_zero_count']}")

    # Step 5: Export data layers
    print("\n💾 Step 5: Exporting data layers...")
    exported_files = integrator.export_data_layers(integrated_data)

    for layer_name, file_path in exported_files.items():
        print(f"   ✓ {layer_name}: {file_path}")

    print("\n🎉 Workflow complete!")
    print("\n🚀 To launch the interactive dashboard:")
    print("   python cascadia.py dashboard")

if __name__ == '__main__':
    basic_workflow()
