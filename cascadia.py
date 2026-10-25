#!/usr/bin/env python3
"""
Cascadia: Geospatial Data Integration and Visualization System

A comprehensive system for integrating different geospatial data sources
using H3 geospatial indexing with an interactive dashboard for visualization.

Usage:
    python cascadia.py acquire --sources earthquakes us_states
    python cascadia.py process --sources earthquakes --force
    python cascadia.py integrate --sources earthquakes us_states
    python cascadia.py dashboard --host 127.0.0.1 --port 8050
"""

import argparse
import logging
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.data.acquisition import DataAcquirer
from src.data.processing import DataProcessor
from src.data.integration import DataIntegrator
from src.visualization.dashboard import CascadiaDashboard
from src.utils.config import config, logger

def _validate_sources(sources: list) -> None:
    """Exit with error if any source is not configured."""
    known_sources = set(config.data_sources.keys())
    unknown = [s for s in sources if s not in known_sources]
    if unknown:
        logger.error(f"Unknown data source(s): {', '.join(unknown)}; "
                     f"configured sources: {', '.join(sorted(known_sources))}")
        sys.exit(2)

def acquire_data(sources: list, force_download: bool = False):
    """Acquire data for specified sources."""
    logger.info(f"Acquiring data for sources: {sources}")

    _validate_sources(sources)

    acquirer = DataAcquirer()
    results = {}
    for source_name in sources:
        results[source_name] = acquirer.acquire_data_source(
            source_name, force_download=force_download
        )

    successful = 0
    for source_name, file_path in results.items():
        if file_path:
            logger.info(f"✓ {source_name}: {file_path}")
            successful += 1
        else:
            logger.error(f"✗ {source_name}: Failed to acquire")

    logger.info(f"Acquisition complete: {successful}/{len(sources)} sources successful")

def process_data(sources: list, force_reprocess: bool = False):
    """Process data for specified sources."""
    logger.info(f"Processing data for sources: {sources}")

    _validate_sources(sources)

    processor = DataProcessor()
    results = {}

    for source_name in sources:
        logger.info(f"Processing {source_name}...")
        df = processor.process_data_source(source_name, force_reprocess=force_reprocess)
        results[source_name] = df

        if df is not None:
            logger.info(f"✓ {source_name}: {len(df)} H3 cells processed")
        else:
            logger.error(f"✗ {source_name}: Processing failed")

    return results

def integrate_data(sources: list, composite_metrics: dict = None):
    """Integrate processed data sources."""
    logger.info(f"Integrating data for sources: {sources}")

    _validate_sources(sources)

    integrator = DataIntegrator()

    # Create visualization dataset
    gdf = integrator.create_visualization_dataset(sources, composite_metrics)

    if gdf is not None:
        logger.info(f"✓ Integration complete: {len(gdf)} features created")

        # Generate summary
        summary = integrator.get_data_summary(gdf)
        logger.info(f"Data summary: {summary['total_h3_cells']} H3 cells")
        for column in summary['columns']:
            if column in summary['summary_stats']:
                stats = summary['summary_stats'][column]
                logger.info(f"  {column}: {stats['mean']:.2f} (min: {stats['min']}, max: {stats['max']})")

        return gdf
    else:
        logger.error("✗ Integration failed")
        return None

def run_dashboard(host: str = '127.0.0.1', port: int = 8050, debug: bool = False):
    """Run the interactive dashboard."""
    logger.info(f"Starting dashboard on {host}:{port}")

    dashboard = CascadiaDashboard()
    dashboard.run(host=host, port=port, debug=debug)

def run_tests():
    """Run the test suite."""
    logger.info("Running test suite...")

    import subprocess
    import sys

    try:
        result = subprocess.run([
            sys.executable, "-m", "pytest",
            "tests/", "-v", "--tb=short"
        ], cwd=Path(__file__).parent)

        if result.returncode == 0:
            logger.info("✓ All tests passed")
        else:
            logger.error("✗ Some tests failed")
            sys.exit(result.returncode)

    except FileNotFoundError:
        logger.error("pytest not found. Install with: uv add --dev pytest")
        sys.exit(1)

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Cascadia: Geospatial Data Integration and Visualization System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s acquire --sources earthquakes us_states
  %(prog)s process --sources earthquakes --force
  %(prog)s integrate --sources earthquakes us_states
  %(prog)s dashboard --port 8050
  %(prog)s test
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Acquire command
    acquire_parser = subparsers.add_parser('acquire', help='Acquire data sources')
    acquire_parser.add_argument('--sources', nargs='+', required=True,
                               help='Data sources to acquire')
    acquire_parser.add_argument('--force', action='store_true',
                               help='Force download even if files exist')

    # Process command
    process_parser = subparsers.add_parser('process', help='Process data sources')
    process_parser.add_argument('--sources', nargs='+', required=True,
                               help='Data sources to process')
    process_parser.add_argument('--force', action='store_true',
                               help='Force reprocessing even if cached')

    # Integrate command
    integrate_parser = subparsers.add_parser('integrate', help='Integrate data sources')
    integrate_parser.add_argument('--sources', nargs='+', required=True,
                                 help='Data sources to integrate')
    integrate_parser.add_argument('--metrics', nargs='*',
                                 help='Composite metrics to create (key=expression)')

    # Dashboard command
    dashboard_parser = subparsers.add_parser('dashboard', help='Run interactive dashboard')
    dashboard_parser.add_argument('--host', default='127.0.0.1',
                                 help='Host to bind dashboard to')
    dashboard_parser.add_argument('--port', type=int, default=8050,
                                 help='Port for dashboard')
    dashboard_parser.add_argument('--debug', action='store_true',
                                 help='Enable debug mode')

    # Test command
    test_parser = subparsers.add_parser('test', help='Run test suite')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # Execute command
    if args.command == 'acquire':
        acquire_data(args.sources, args.force)

    elif args.command == 'process':
        process_data(args.sources, args.force)

    elif args.command == 'integrate':
        composite_metrics = {}
        if args.metrics:
            for metric in args.metrics:
                if '=' in metric:
                    key, expression = metric.split('=', 1)
                    composite_metrics[key.strip()] = expression.strip()

        integrate_data(args.sources, composite_metrics)

    elif args.command == 'dashboard':
        run_dashboard(args.host, args.port, args.debug)

    elif args.command == 'test':
        run_tests()

if __name__ == '__main__':
    main()
