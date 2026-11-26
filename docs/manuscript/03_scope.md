# Interpretation and scope

The result of spatial alignment depends on the selected resolution, geometry
support, value column, and aggregation rule. An outer join currently replaces
missing values with zero. This makes absent observations indistinguishable from
zeros in the joined numeric output.

Live data availability and provider schemas can change. The built-in
state-density fallback is a placeholder derived from geographic area, and a
sum of earthquake magnitudes is neither an event count nor an energy
measurement. Cascadia provides a data-integration and visualization pipeline.
Application-specific units, data quality, and interpretation remain the
responsibility of the analysis using it.
