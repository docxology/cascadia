# Cascadia: Geospatial Data Integration and Visualization System

A comprehensive, modular system for integrating different geospatial data sources using H3 geospatial indexing with an interactive dashboard for visualization.

## Features

- **Modular Architecture**: Clean, testable modules for data acquisition, processing, and visualization
- **H3 Integration**: Uses H3 geospatial indexing for efficient spatial operations and analysis
- **Skip Logic**: Intelligent caching system that skips redundant downloads and processing
- **Interactive Dashboard**: Dash-based interface with clickable toggle layers
- **Test-Driven**: 100% test coverage with comprehensive test suite
- **Environment Management**: Uses `uv` for streamlined dependency management

## Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/cascadia.git
   cd cascadia
   ```

2. **Set up environment with uv:**
   ```bash
   uv sync
   ```

3. **Activate environment:**
   ```bash
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```

## Project Structure

```
cascadia/
├── src/
│   ├── data/
│   │   ├── acquisition.py      # Data downloading and retrieval
│   │   ├── processing.py       # Data cleaning and H3 integration
│   │   └── integration.py      # Data merging and preparation
│   ├── visualization/
│   │   ├── dashboard.py        # Interactive dashboard
│   │   └── layers.py           # Toggle layer management
│   └── utils/
│       ├── h3_utils.py         # H3 geospatial utilities
│       └── config.py           # Configuration management
├── tests/
│   ├── test_*.py              # Comprehensive test suite
├── data/
│   ├── raw/                   # Downloaded source data
│   ├── processed/             # Processed and H3-indexed data
│   └── cache/                 # Skip logic cache files
├── docs/
│   └── examples/              # Usage examples and tutorials
├── cascadia.py                # Main entry point script
├── .cursorrules              # Project guidelines and rules
└── README.md                 # This file
```

## Usage

### Command Line Interface

The system provides a comprehensive CLI for all operations:

```bash
# Acquire data sources
python cascadia.py acquire --sources population infrastructure

# Process data with H3 integration
python cascadia.py process --sources population --force

# Integrate multiple data sources
python cascadia.py integrate --sources population infrastructure

# Run interactive dashboard
python cascadia.py dashboard --port 8050

# Run test suite
python cascadia.py test
```

### Data Flow

The system follows a clear data pipeline:

1. **Subfolders**: Data sources are organized in structured subfolders
2. **Download**: Raw data is downloaded from configured sources
3. **Process**: Data is cleaned, standardized, and converted to H3 indexing
4. **Skip Logic**: System checks for existing processed data and skips redundant operations
5. **Integration**: Multiple data sources are merged and composite metrics created
6. **Dashboard**: Interactive visualization with clickable toggle layers

### Configuration

Data sources are configured in `src/utils/config.py`:

```python
DATA_SOURCES = {
    "population": {
        "url": "https://example.com/population.geojson",
        "format": "geojson",
        "description": "Global population density data"
    },
    "infrastructure": {
        "url": "https://example.com/infrastructure.geojson",
        "format": "geojson",
        "description": "Infrastructure network data"
    }
}
```

## API Usage

### Data Acquisition

```python
from src.data.acquisition import DataAcquirer

acquirer = DataAcquirer()
file_path = acquirer.acquire_data_source('population', force_download=False)
```

### Data Processing

```python
from src.data.processing import DataProcessor

processor = DataProcessor()
h3_dataframe = processor.process_data_source('population', 'population_density')
```

### Data Integration

```python
from src.data.integration import DataIntegrator

integrator = DataIntegrator()
composite_metrics = {'total_score': 'population_density + infrastructure_score'}
integrated_data = integrator.create_visualization_dataset(
    ['population', 'infrastructure'],
    composite_metrics
)
```

### Interactive Dashboard

```python
from src.visualization.dashboard import CascadiaDashboard

dashboard = CascadiaDashboard()
dashboard.run(host='127.0.0.1', port=8050, debug=False)
```

## Testing

Run the comprehensive test suite:

```bash
python cascadia.py test
```

Or run specific tests:

```bash
python -m pytest tests/test_h3_utils.py -v
```

## Development

### Adding New Data Sources

1. Add configuration to `src/utils/config.py`
2. Implement any custom processing logic in `src/data/processing.py`
3. Add integration logic in `src/data/integration.py`
4. Create comprehensive tests in `tests/`

### Environment Variables

- `H3_RESOLUTION`: Default H3 resolution (default: 9)
- `MAX_DOWNLOAD_RETRIES`: Maximum download retry attempts (default: 3)
- `REQUEST_TIMEOUT`: HTTP request timeout in seconds (default: 30)

### Best Practices

- All code follows modular, functional programming principles
- Test-driven development with 100% coverage
- Real data analysis (no mock methods)
- Clear documentation with "show not tell" approach
- Professional, concise, and elegant code style

## Examples

### Basic Data Integration

```python
# Acquire and process population data
python cascadia.py acquire --sources population
python cascadia.py process --sources population

# Acquire and process infrastructure data
python cascadia.py acquire --sources infrastructure
python cascadia.py process --sources infrastructure

# Integrate both datasets
python cascadia.py integrate --sources population infrastructure

# Launch dashboard
python cascadia.py dashboard
```

### Advanced Integration with Composite Metrics

```python
# Integrate with custom composite metrics
python cascadia.py integrate \
    --sources population infrastructure \
    --metrics "accessibility_score=(population_density * 0.4 + infrastructure_score * 0.6)"
```

### Custom Development

```python
# Custom data processing workflow
from cascadia import acquire_data, process_data, integrate_data, run_dashboard

# Your custom workflow
acquire_data(['population', 'infrastructure'])
process_data(['population', 'infrastructure'])
integrated = integrate_data(['population', 'infrastructure'])
run_dashboard()
```

## Dependencies

- **h3**: H3 geospatial indexing
- **pandas**: Data manipulation
- **geopandas**: Geospatial data handling
- **numpy**: Numerical computing
- **matplotlib**: Plotting
- **plotly**: Interactive visualizations
- **dash**: Web dashboard framework
- **requests**: HTTP requests

## Contributing

1. Follow the `.cursorrules` guidelines
2. Write tests for all new functionality
3. Use modular, functional programming approach
4. Document with examples, not explanations
5. Ensure all tests pass before submitting

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- H3 geospatial indexing system
- Dash framework for interactive visualizations
- uv for Python environment management
