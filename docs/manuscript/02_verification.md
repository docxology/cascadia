# Verification with synthetic data

The offline example in `docs/examples/basic_workflow.py` starts with two
nearby synthetic points. At H3 resolution nine, the program aggregates two
value columns separately, joins them by cell, and checks that their totals
remain seven and two. It writes each layer into a temporary directory and
reads the GeoJSON back to confirm that it carries the expected cell key.

The native suite separately checks download handling, configuration,
geometry conversion, aggregation, joining, export, and dashboard behavior
using local test inputs. The manuscript rebuild uses the checked-in
architecture diagram. The synthetic values and schematic diagram explain
the workflow without implying that live inputs were collected for this note.
