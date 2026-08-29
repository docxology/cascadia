# cascadia — Agent Guide

## Layout

| Path | Purpose |
|---|---|
| `cascadia.py` | Thin CLI entry point; dispatches subcommands to `src/` |
| `src/data/` | `acquisition.py` (downloads), `processing.py` (cleaning + H3), `integration.py` (merging) |
| `src/visualization/` | `dashboard.py` (Dash app), `layers.py` (toggle layers) |
| `src/utils/` | `h3_utils.py`, `config.py` — `DATA_SOURCES` dict defines the pipeline inputs |
| `tests/` | pytest suite (root `README.md` claims full coverage) |
| `data/` | Local `raw/`, `processed/`, `cache/` trees; safe to regenerate |

## Conventions observed in this repo

- Environment and dependency management via `uv` (`uv sync`; `pyproject.toml`).
- Skip logic: processing steps check `data/` for existing outputs before redoing work.
- Root `README.md` is the authoritative user/CLI reference; keep this file to
  pointers, not duplicates.

## How docs here are maintained

- `docs/README.md` is the human entry point; keep the map and commands in sync
  with `cascadia.py` subcommands and `pyproject.toml`.
- Copy commands from the code, never invent flags.

## Notes for agents

- Do not commit anything under `data/` (downloaded/cached data).
- Verify CLI examples against `cascadia.py` before editing them.
