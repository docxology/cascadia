# Build and verify the Cascadia manuscript

Install Git, uv, `rsvg-convert` from librsvg, Pandoc, and XeLaTeX with the
[template's required TeX packages](https://github.com/docxology/template/blob/87704feae0a4490ef7dad9c931d268e8c30273c2/docs/usage/output-formats.md).
The verified environment uses Pandoc 3.14 and pandoc-crossref 0.3.26b built
against it. The template engine uses Python 3.14 or later.

From a clean Cascadia checkout, clone the pinned renderer and put a detached
project copy under its `projects/working/` directory.

```sh
project_root="$(pwd -P)"
work_directory="$(mktemp -d)"
renderer="$work_directory/template"
git clone https://github.com/docxology/template.git "$renderer"
git -C "$renderer" checkout --detach 87704feae0a4490ef7dad9c931d268e8c30273c2
mkdir -p "$renderer/projects/working"
project_copy="$renderer/projects/working/cascadia"
git clone --no-hardlinks "$project_root" "$project_copy"
git -C "$project_copy" checkout --detach "$(git -C "$project_root" rev-parse HEAD)"

cd "$project_copy"
mkdir -p output/figures
rsvg-convert docs/assets/overview.svg -o output/figures/cascadia-overview.png
cp docs/manuscript/figure_registry.json output/figures/
cd "$renderer"
uv sync --locked --no-dev
uv run --no-sync python scripts/pipeline/stage_03_render.py --project working/cascadia
uv run --no-sync python scripts/pipeline/stage_04_validate.py --project working/cascadia
```

The build uses the [canonical manuscript](manuscript/README.md) and the
checked-in architecture diagram. It needs no downloaded geospatial inputs.
In `"$project_copy"`, inspect `output/pdf/cascadia_combined.pdf` and
`output/web/index.html` for all sections, citations, and the workflow figure.
Review the validation report and rendered provenance under `output/reports/`.
The [usage guide](usage.md) has the standalone software checks.
