# cascadia — Documentation

Geospatial data integration and visualization system: it downloads configured
geospatial sources, cleans and indexes them with H3, merges them, and serves an
interactive Dash dashboard with toggle layers.

## Repository map

- `cascadia.py` — CLI entry point (acquire / process / integrate / dashboard / test)
- `src/data/` — acquisition, processing, integration modules
- `src/visualization/` — dashboard and toggle-layer modules
- `src/utils/` — H3 utilities and `config.py` (data-source configuration)
- `tests/` — test suite
- `data/` — `raw/`, `processed/`, `cache/` (downloads and skip-logic cache)
- `docs/examples/` — usage examples (`basic_workflow.py`, `custom_processing.py`)

## Running

```bash
uv sync
python cascadia.py acquire --sources population infrastructure
python cascadia.py process --sources population --force
python cascadia.py integrate --sources population infrastructure
python cascadia.py dashboard --port 8050
python cascadia.py test
```

See the root `README.md` for the full CLI, API, and configuration reference.

## Example notebooks / scripts

Runnable usage examples live in [`examples/`](examples/) — start with
`basic_workflow.py`.
