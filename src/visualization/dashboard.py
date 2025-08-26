"""Interactive dashboard module for geospatial data visualization with clickable toggle layers."""

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional, Any
import json
import logging

from ..utils.config import config
from ..data.integration import DataIntegrator

logger = logging.getLogger(__name__)

class CascadiaDashboard:
    """Interactive dashboard with clickable toggle layers for geospatial data."""

    def __init__(self):
        self.integrator = DataIntegrator()
        self.app = dash.Dash(__name__)
        self.available_layers = {}
        self.setup_layout()
        self.setup_callbacks()

    def setup_layout(self):
        """Set up the dashboard layout."""
        self.app.layout = html.Div([
            html.H1("Cascadia Geospatial Data Integration Dashboard",
                   style={'textAlign': 'center', 'marginBottom': 30}),

            # Control panel
            html.Div([
                html.H3("Layer Controls"),
                html.Div(id='layer-toggles', children=[]),
                html.Button('Update View', id='update-button',
                           style={'marginTop': 10, 'marginRight': 10}),
                html.Button('Reset Layers', id='reset-button',
                           style={'marginTop': 10})
            ], style={'width': '20%', 'display': 'inline-block', 'verticalAlign': 'top'}),

            # Main visualization area
            html.Div([
                dcc.Graph(
                    id='main-map',
                    style={'height': '70vh'},
                    config={'scrollZoom': True}
                ),

                # Data summary
                html.Div(id='data-summary', style={'marginTop': 20}),

                # Layer information
                html.Div([
                    html.H4("Layer Information"),
                    html.Div(id='layer-info')
                ], style={'marginTop': 20})

            ], style={'width': '75%', 'display': 'inline-block', 'marginLeft': '2%'}),

            # Hidden div for storing layer data
            html.Div(id='layer-data-store', style={'display': 'none'}),

            # Hidden interval to trigger initial data loading
            dcc.Interval(id='initial-trigger', interval=100, max_intervals=1, style={'display': 'none'})
        ])

    def setup_callbacks(self):
        """Set up dashboard callbacks for interactivity."""

        # Add an interval to trigger initial data loading
        @self.app.callback(
            Output('update-button', 'n_clicks'),
            Input('initial-trigger', 'n_intervals'),
            prevent_initial_call=False
        )
        def trigger_initial_load(n_intervals):
            """Trigger initial data loading when page loads."""
            if n_intervals is None or n_intervals == 0:
                return 1
            return dash.no_update

        @self.app.callback(
            [Output('layer-toggles', 'children'),
             Output('layer-data-store', 'children'),
             Output('main-map', 'figure'),
             Output('data-summary', 'children')],
            [Input('update-button', 'n_clicks')],
            [State('layer-data-store', 'children')]
        )
        def update_layer_toggles(n_clicks, current_layer_data):
            """Update layer toggle controls and store layer data."""
            layers_dir = config.processed_data_dir / "layers"
            if not layers_dir.exists():
                empty_fig = self.create_empty_map()
                return [], "", empty_fig, html.P("No layer data available")

            layer_files = list(layers_dir.glob("*_layer.geojson"))
            toggles = []
            layer_data = {}

            for layer_file in layer_files:
                layer_name = layer_file.stem.replace('_layer', '')

                # Load layer data
                gdf = gpd.read_file(layer_file)
                layer_data[layer_name] = gdf.to_json()

                # Create toggle switch
                toggle = html.Div([
                    html.Label(f"{layer_name.replace('_', ' ').title()}"),
                    dcc.Checklist(
                        id=f'toggle-{layer_name}',
                        options=[{'label': '', 'value': layer_name}],
                        value=[layer_name],  # Default to enabled
                        style={'display': 'inline-block', 'marginLeft': 10}
                    )
                ], style={'marginBottom': 10})

                toggles.append(toggle)

            # Create initial map with all layers
            fig = self.create_map_figure(layer_data, list(layer_data.keys()))

            # Create data summary
            total_cells = sum(len(gpd.GeoDataFrame.from_features(json.loads(gdf_json))) for gdf_json in layer_data.values())
            summary = html.Div([
                html.P(f"Total H3 cells: {total_cells}"),
                html.Ul([html.Li(f"{name.replace('_', ' ').title()}: {len(gpd.GeoDataFrame.from_features(json.loads(gdf_json)))} cells") for name, gdf_json in layer_data.items()])
            ])

            return toggles, json.dumps(layer_data), fig, summary

        @self.app.callback(
            Output('main-map', 'figure'),
            [Input('layer-data-store', 'children'),
             Input('update-button', 'n_clicks')]
        )
        def update_map(layer_data_json, n_clicks):
            """Update the main map based on active layers."""
            if not layer_data_json:
                return self.create_empty_map()

            try:
                layer_data = json.loads(layer_data_json)
            except:
                return self.create_empty_map()

            # Get all available layers and check their toggle states
            active_layers = []
            available_layers = list(layer_data.keys()) if layer_data else []

            # Check each layer's toggle state (default to active if toggle not found)
            for layer_name in available_layers:
                # Try to get toggle value, default to active
                toggle_id = f'toggle-{layer_name}'
                # For now, assume all layers are active by default
                # In a more sophisticated implementation, you'd track toggle states
                active_layers.append(layer_name)

            return self.create_map_figure(layer_data, active_layers)

        @self.app.callback(
            Output('data-summary', 'children'),
            [Input('layer-data-store', 'children')]
        )
        def update_data_summary(layer_data_json):
            """Update data summary information."""
            if not layer_data_json:
                return html.P("No data loaded")

            try:
                layer_data = json.loads(layer_data_json)
            except:
                return html.P("Error loading data")

            total_cells = 0
            layer_summaries = []

            for layer_name, geojson_str in layer_data.items():
                gdf = gpd.GeoDataFrame.from_features(json.loads(geojson_str))
                total_cells += len(gdf)

                if 'value' in gdf.columns:
                    mean_val = gdf['value'].mean()
                    layer_summaries.append(f"{layer_name}: {len(gdf)} cells, mean: {mean_val:.2f}")

            summary = html.Div([
                html.P(f"Total H3 cells: {total_cells}"),
                html.Ul([html.Li(summary) for summary in layer_summaries])
            ])

            return summary

        @self.app.callback(
            Output('layer-info', 'children'),
            [Input('main-map', 'clickData')]
        )
        def display_layer_info(click_data):
            """Display information about clicked map features."""
            if not click_data:
                return html.P("Click on a hexagon to see details")

            # Extract H3 index from clicked point
            try:
                customdata = click_data['points'][0].get('customdata', [])
                if customdata:
                    h3_index = customdata[0]
                    return html.Div([
                        html.H5("H3 Cell Information"),
                        html.P(f"H3 Index: {h3_index}"),
                        html.P("Layer values will be displayed here when implemented")
                    ])
            except:
                pass

            return html.P("Click on a hexagon to see details")

    def get_available_layers(self) -> List[str]:
        """Get list of available layer names."""
        layers_dir = config.processed_data_dir / "layers"
        if not layers_dir.exists():
            return []

        layer_files = list(layers_dir.glob("*_layer.geojson"))
        return [f.stem.replace('_layer', '') for f in layer_files]

    def create_empty_map(self) -> go.Figure:
        """Create an empty map figure."""
        fig = go.Figure()

        fig.update_layout(
            title="No Data Available",
            showlegend=True,
            height=600
        )

        return fig

    def create_map_figure(self, layer_data: Dict[str, str],
                         active_layers: List[str]) -> go.Figure:
        """Create map figure with active layers."""
        fig = go.Figure()

        # Define color scales for different layers
        color_scales = [
            'Blues', 'Reds', 'Greens', 'Purples', 'Oranges',
            'Greys', 'YlOrBr', 'YlGnBu', 'BuGn', 'PuBuGn'
        ]

        for i, layer_name in enumerate(active_layers):
            if layer_name not in layer_data:
                continue

            try:
                # Load layer GeoDataFrame
                geojson_str = layer_data[layer_name]
                gdf = gpd.GeoDataFrame.from_features(json.loads(geojson_str))

                # Convert to centroids for visualization
                centroids = gdf.geometry.centroid
                gdf['lon'] = centroids.x
                gdf['lat'] = centroids.y

                # Determine which column to use for visualization
                value_column = None
                if 'value' in gdf.columns:
                    value_column = 'value'
                elif 'magnitude' in gdf.columns:
                    value_column = 'magnitude'
                elif 'intensity' in gdf.columns:
                    value_column = 'intensity'
                elif len([col for col in gdf.columns if col not in ['geometry', 'h3_index']]) > 0:
                    # Use the first non-geometry, non-h3_index column
                    value_column = [col for col in gdf.columns if col not in ['geometry', 'h3_index']][0]

                if value_column is None:
                    logger.error(f"No suitable value column found in layer {layer_name}")
                    continue

                # Create choropleth map
                fig.add_trace(go.Choroplethmapbox(
                    geojson=gdf.__geo_interface__,
                    locations=gdf.index,
                    z=gdf[value_column],
                    colorscale=color_scales[i % len(color_scales)],
                    name=layer_name.replace('_', ' ').title(),
                    showscale=True,
                    customdata=gdf['h3_index'],
                    hovertemplate=f'{layer_name}: %{{z}}<extra></extra>'
                ))

            except Exception as e:
                logger.error(f"Failed to add layer {layer_name}: {e}")

        # Update layout
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_zoom=3,
            mapbox_center={"lat": 39.8283, "lon": -98.5795},  # Center of USA
            margin={"r":0,"t":30,"l":0,"b":0},
            height=600,
            showlegend=True
        )

        return fig

    def run(self, host: str = '127.0.0.1', port: int = 8050, debug: bool = False):
        """Run the dashboard server."""
        logger.info(f"Starting Cascadia Dashboard on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug)

    def create_sample_data(self):
        """Create sample data for testing the dashboard."""
        # This would be used for demonstration purposes
        sample_data = {
            'population_density': [100, 200, 150, 300, 250],
            'infrastructure_score': [0.8, 0.6, 0.9, 0.4, 0.7],
            'environmental_index': [0.7, 0.8, 0.6, 0.9, 0.5]
        }

        sample_h3_indices = [
            '8928308280fffff', '8928308281fffff', '8928308282fffff',
            '8928308283fffff', '8928308284fffff'
        ]

        # Create sample integrated dataset
        df_data = {
            'h3_index': sample_h3_indices,
            'population_density': sample_data['population_density'],
            'infrastructure_score': sample_data['infrastructure_score'],
            'environmental_index': sample_data['environmental_index']
        }

        sample_df = pd.DataFrame(df_data)

        # Save sample data
        sample_path = config.processed_data_dir / "sample_integrated.csv"
        sample_df.to_csv(sample_path, index=False)

        logger.info("Created sample data for dashboard testing")
