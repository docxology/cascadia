# Pipeline and data contracts

Acquisition retrieves files from configured endpoints and keeps local
records so unchanged inputs can be reused. The earthquake source uses the
USGS GeoJSON feed [@usgs-feed]. Processing normalizes supported inputs to
WGS 84 and removes null and duplicate geometries. H3 assigns a cell key
to each point or supplies a polygon cover for supported polygon inputs
[@h3-docs]. Cell-level aggregation uses the configured value column.

![Cascadia moves from cached acquisition through H3 processing and integration to separately exported layers in Dash.](../../output/figures/cascadia-overview.png){#fig:cascadia-overview}

The integrator joins processed data by the `h3_index` key and prefixes the
value column with its source name. It reconstructs cell geometries in the
integrated GeoJSON and can export numeric columns as separate GeoJSON files.
The Dash interface [@dash-docs] discovers these layer files and exposes
them through map controls.
