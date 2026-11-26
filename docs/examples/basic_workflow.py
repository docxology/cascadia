"""Run the point-to-layer workflow using synthetic data and a temporary directory."""

from pathlib import Path
from tempfile import TemporaryDirectory

import geopandas as gpd

from src.data.integration import DataIntegrator
from src.utils.h3_utils import H3Processor


def basic_workflow() -> None:
    """Aggregate two synthetic layers, join them by H3 cell, and export each."""
    points = gpd.points_from_xy([-122.33, -122.33001], [47.61, 47.61001])
    samples = gpd.GeoDataFrame(
        {"first": [3, 4], "second": [1, 1]}, geometry=points, crs="EPSG:4326"
    )
    processor = H3Processor(resolution=9)
    layer_names = ("first", "second")
    indexed = {
        name: processor.aggregate_points_to_h3(samples, name)
        for name in layer_names
    }
    integrator = DataIntegrator()
    joined = integrator.merge_h3_data(indexed)
    assert joined["first_value"].sum() == 7
    assert joined["second_value"].sum() == 2
    spatial = processor.h3_dataframe_to_geodataframe(joined)

    with TemporaryDirectory() as destination:
        paths = integrator.export_data_layers(spatial, Path(destination))
        for name in layer_names:
            layer = gpd.read_file(paths[f"{name}_value"])
            assert layer["h3_index"].tolist() == joined["h3_index"].tolist()
            print(f"{name}: {len(layer)} H3 cell(s), total {layer['value'].sum()}")


if __name__ == "__main__":
    basic_workflow()
