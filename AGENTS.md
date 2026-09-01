# cascadia — Agent Guide

LOCAL-ONLY lane under `projects/ongoing/Cascadia/Crescent_City` view:
`/Volumes/external_drive/Git/template/projects/ongoing/Crescent_City/cascadia`
(symlink → `/Volumes/external_drive/Git/projects/ongoing/docxology/cascadia`).
Never commit anything here. Parent policy: `../AGENTS.md`.

## What this is

H3-based geospatial data integration and visualization system (Python/uv):
acquire raw geodata (earthquakes, states, cities), process into H3 cells,
integrate layers, and view in a Dash dashboard with toggleable layers.

## Layout (verified on disk)

| Path | Purpose |
|---|---|
| `cascadia.py` | Real CLI entry point (argparse): acquire / process / integrate / dashboard / test. Fixed 2026-08-31: `acquire --sources` now filters to the named sources (unknown names exit 2 with the configured list). |
| `main.py` | Stub — prints "Hello from cascadia!" only; not a real entry point. |
| `test_*.py` (root) | Three root-level test scripts: test_complete_dashboard.py, test_dashboard_layers.py, test_data_reading.py (unverified whether run in CI) |
| `debug_dashboard.py` | Dashboard debugging script (unverified) |
| `src/data/` | acquisition.py, processing.py, integration.py |
| `src/visualization/` | dashboard.py (Dash app), layers.py |
| `src/utils/` | h3_utils.py, config.py (DATA_SOURCES defines pipeline inputs) |
| `tests/` | pytest suite: test_acquisition, test_config, test_dashboard, test_h3_utils, test_integration, test_layers, test_processing |
| `data/` | raw/, processed/ (+processed/layers/), cache/ — regeneratable |
| `docs/` | README.md, AGENTS.md, examples/, manuscript/ |

## Gotchas

- Root `README.md` claims "100% test coverage" — unverified claim; do not repeat it in prose without running the suite.
- `main.py` is a uv-scaffold stub, not the pipeline entry point.
- Do not commit anything under `data/`.
- `__pycache__` dirs are out of scope for documentation.

## Verify

```bash
uv sync
uv run pytest tests/
```
