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
|`test_*.py`, `debug_dashboard.py` (root)|Manual smoke/debug scripts; not collected by pytest (`testpaths = ["tests"]`), and they need generated layers under `data/processed/layers/`.|
| `src/data/` | acquisition.py, processing.py, integration.py |
| `src/visualization/` | dashboard.py (Dash app), layers.py |
| `src/utils/` | h3_utils.py, config.py (DATA_SOURCES defines pipeline inputs) |
| `tests/` | pytest suite: test_acquisition, test_config, test_dashboard, test_h3_utils, test_integration, test_layers, test_processing |
| `data/` | raw/, processed/ (+processed/layers/), cache/ — regeneratable |
| `docs/` | README.md, AGENTS.md, examples/, manuscript/ |

## Gotchas

- The suite is run with `uv run pytest tests/`; no coverage percentage is measured, so do not claim one.
- Do not commit anything under `data/`.
- `__pycache__` dirs are out of scope for documentation.

## Verify

```bash
uv sync
uv run pytest tests/
```
