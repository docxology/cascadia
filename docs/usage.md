# Install and use Cascadia

Run commands from the checkout root. The package declares Python 3.13 or
later. These reproducible commands use Python 3.13 and the committed lockfile.

```sh
uv sync --locked --python 3.13
uv run --no-sync --python 3.13 python cascadia.py --help
uv run --no-sync --python 3.13 pytest tests/
```

## Try the offline example

```sh
uv run --no-sync --python 3.13 python -m docs.examples.basic_workflow
```

The example passes two synthetic point layers through the H3 aggregator and
outer join. It checks distinct source totals and writes demonstration GeoJSON
layers in a temporary directory. The example uses no live data.

## Run the CLI on configured inputs

The `acquire`, `process`, and `integrate` commands accept the sources
`earthquakes`, `us_states`, and `world_cities`. Unknown names exit with
status 2. These example commands use the public USGS feed configured in
[`src/utils/config.py`](../src/utils/config.py).

```sh
uv run --no-sync --python 3.13 python cascadia.py acquire --sources earthquakes
uv run --no-sync --python 3.13 python cascadia.py process --sources earthquakes
uv run --no-sync --python 3.13 python cascadia.py integrate --sources earthquakes
```

Acquisition depends on availability and schema compatibility at the upstream
URL. Acquisition and processing accept `--force` to bypass local reuse. The
integrator accepts `--metrics` with trusted `name=expression` arguments. It
logs failed expressions and can continue with the remaining columns.

| Surface | Behavior |
| --- | --- |
| `data/raw/` | Acquired source files |
| `data/cache/` | Local acquisition and processing records |
| `data/processed/<source>_processed.h3` | CSV with H3 cell IDs and aggregated values |
| `data/processed/integrated_dataset.geojson` | Integrated H3 cell geometries and source columns |
| `data/processed/layers/` | Separate GeoJSON layers written by the Python layer-export API and discovered by the dashboard |

Export layers after integration using the same Python environment.

```sh
uv run --no-sync --python 3.13 python - <<'PY'
from src.data.integration import DataIntegrator

integrator = DataIntegrator()
dataset = integrator.create_visualization_dataset(["earthquakes"])
if dataset is None:
    raise SystemExit("Process the earthquakes source first")
integrator.export_data_layers(dataset)
PY
uv run --no-sync --python 3.13 python cascadia.py dashboard --host 127.0.0.1 --port 8050
```

Open `http://127.0.0.1:8050` and select an exported layer. The dashboard also
includes illustrative sample data.

## Configuration and interpretation

`H3_RESOLUTION` defaults to `9`, `MAX_DOWNLOAD_RETRIES` to `3`, and
`REQUEST_TIMEOUT` to `30` seconds. These settings come from the environment.
Reprocess with `--force` after changing resolution. Use a lower resolution
when exploring large polygon inputs to control the number of cells.

An outer join fills missing values with zero. Preserve missingness in any
analysis that needs to distinguish a measurement of zero from an absent source.
The fallback State density is a placeholder, and aggregated earthquake
magnitudes are software output values. See the [manuscript's scope](manuscript/03_scope.md)
and the [backlog](../TODO.md) before treating outputs as measurements.

The [custom-processing example](examples/custom_processing.py) sketches how to
extend the processor and integrator. Its environmental configuration and
records must be supplied separately.
