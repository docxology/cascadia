"""Layer management module for handling clickable toggle layers in the dashboard."""

import pandas as pd
import geopandas as gpd
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import json
import logging

from ..utils.config import config

logger = logging.getLogger(__name__)

class LayerManager:
    """Manages visualization layers with toggle functionality."""

    def __init__(self):
        self.active_layers: Set[str] = set()
        self.layer_metadata: Dict[str, Dict[str, Any]] = {}
        self.layers_dir = config.processed_data_dir / "layers"

    def discover_layers(self) -> List[str]:
        """Discover available layers from the layers directory."""
        if not self.layers_dir.exists():
            return []

        layer_files = list(self.layers_dir.glob("*_layer.geojson"))
        layer_names = []

        for layer_file in layer_files:
            layer_name = layer_file.stem.replace('_layer', '')
            layer_names.append(layer_name)

            # Load metadata
            self.load_layer_metadata(layer_name, layer_file)

        return layer_names

    def load_layer_metadata(self, layer_name: str, layer_file: Path) -> bool:
        """Load metadata for a specific layer. Returns True on success."""
        try:
            gdf = gpd.read_file(layer_file)

            metadata = {
                'file_path': layer_file,
                'feature_count': len(gdf),
                'columns': list(gdf.columns),
                'bounds': gdf.total_bounds.tolist() if len(gdf) > 0 else None,
                'value_range': None,
                'geometry_type': gdf.geometry.geom_type.iloc[0] if len(gdf) > 0 else None
            }

            # Calculate value range if 'value' column exists
            if 'value' in gdf.columns:
                metadata['value_range'] = {
                    'min': float(gdf['value'].min()),
                    'max': float(gdf['value'].max()),
                    'mean': float(gdf['value'].mean()),
                    'median': float(gdf['value'].median())
                }

            self.layer_metadata[layer_name] = metadata
            return True

        except Exception as e:
            logger.error(f"Failed to load metadata for layer {layer_name}: {e}")
            return False

    def activate_layer(self, layer_name: str) -> bool:
        """Activate a layer for visualization."""
        if layer_name not in self.layer_metadata:
            if not self.load_layer_metadata(layer_name,
                                          self.layers_dir / f"{layer_name}_layer.geojson"):
                return False

        self.active_layers.add(layer_name)
        logger.info(f"Activated layer: {layer_name}")
        return True

    def deactivate_layer(self, layer_name: str) -> bool:
        """Deactivate a layer from visualization."""
        if layer_name in self.active_layers:
            self.active_layers.remove(layer_name)
            logger.info(f"Deactivated layer: {layer_name}")
            return True
        return False

    def toggle_layer(self, layer_name: str) -> bool:
        """Toggle a layer's active state."""
        if layer_name in self.active_layers:
            return self.deactivate_layer(layer_name)
        else:
            return self.activate_layer(layer_name)

    def get_active_layers(self) -> List[str]:
        """Get list of currently active layers."""
        return list(self.active_layers)

    def get_layer_data(self, layer_name: str) -> Optional[gpd.GeoDataFrame]:
        """Get the data for a specific layer."""
        if layer_name not in self.layer_metadata:
            return None

        try:
            layer_file = self.layer_metadata[layer_name]['file_path']
            return gpd.read_file(layer_file)
        except Exception as e:
            logger.error(f"Failed to load data for layer {layer_name}: {e}")
            return None

    def get_combined_layer_data(self) -> Optional[gpd.GeoDataFrame]:
        """Get combined data for all active layers."""
        if not self.active_layers:
            return None

        combined_gdfs = []

        for layer_name in self.active_layers:
            gdf = self.get_layer_data(layer_name)
            if gdf is not None:
                # Add layer name as a column
                gdf['layer'] = layer_name
                combined_gdfs.append(gdf)

        if not combined_gdfs:
            return None

        # Combine all layers
        combined_gdf = pd.concat(combined_gdfs, ignore_index=True)

        # Group by H3 index and create composite values
        if 'h3_index' in combined_gdf.columns:
            # For now, just keep the first occurrence of each H3 cell
            combined_gdf = combined_gdf.drop_duplicates(subset=['h3_index'])

        return combined_gdf

    def create_layer_composition(self, layer_configs: Dict[str, Dict[str, Any]]) -> str:
        """Create a composition configuration for layer visualization."""
        composition = {
            'active_layers': list(self.active_layers),
            'layer_configs': layer_configs,
            'timestamp': pd.Timestamp.now().isoformat()
        }

        return json.dumps(composition, indent=2)

    def save_layer_state(self, state_file: Optional[Path] = None) -> bool:
        """Save the current layer state to a file."""
        if state_file is None:
            state_file = config.cache_dir / "layer_state.json"

        try:
            state_file.parent.mkdir(parents=True, exist_ok=True)

            state = {
                'active_layers': list(self.active_layers),
                'layer_metadata': self.layer_metadata,
                'timestamp': pd.Timestamp.now().isoformat()
            }

            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)

            logger.info(f"Saved layer state to {state_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to save layer state: {e}")
            return False

    def load_layer_state(self, state_file: Optional[Path] = None) -> bool:
        """Load layer state from a file."""
        if state_file is None:
            state_file = config.cache_dir / "layer_state.json"

        if not state_file.exists():
            return False

        try:
            with open(state_file, 'r') as f:
                state = json.load(f)

            self.active_layers = set(state.get('active_layers', []))
            self.layer_metadata = state.get('layer_metadata', {})

            logger.info(f"Loaded layer state from {state_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to load layer state: {e}")
            return False

    def get_layer_statistics(self) -> Dict[str, Any]:
        """Get statistics for all layers."""
        stats = {
            'total_layers': len(self.layer_metadata),
            'active_layers': len(self.active_layers),
            'layer_details': {}
        }

        for layer_name, metadata in self.layer_metadata.items():
            stats['layer_details'][layer_name] = {
                'is_active': layer_name in self.active_layers,
                'feature_count': metadata.get('feature_count', 0),
                'value_range': metadata.get('value_range'),
                'geometry_type': metadata.get('geometry_type')
            }

        return stats

    def validate_layer_data(self, layer_name: str) -> Dict[str, Any]:
        """Validate the integrity of layer data."""
        validation_result = {
            'layer_name': layer_name,
            'is_valid': False,
            'issues': []
        }

        if layer_name not in self.layer_metadata:
            validation_result['issues'].append('Layer not found in metadata')
            return validation_result

        metadata = self.layer_metadata[layer_name]

        # Check if file exists
        if not metadata['file_path'].exists():
            validation_result['issues'].append('Layer file does not exist')
            return validation_result

        try:
            gdf = self.get_layer_data(layer_name)

            if gdf is None:
                validation_result['issues'].append('Failed to load layer data')
                return validation_result

            # Validate required columns
            required_columns = ['h3_index', 'value', 'geometry']
            missing_columns = [col for col in required_columns if col not in gdf.columns]
            if missing_columns:
                validation_result['issues'].append(f'Missing required columns: {missing_columns}')

            # Validate geometries
            if not gdf.geometry.is_valid.all():
                invalid_count = (~gdf.geometry.is_valid).sum()
                validation_result['issues'].append(f'Found {invalid_count} invalid geometries')

            # Validate H3 indices (real cell validity via the h3 library)
            if 'h3_index' in gdf.columns:
                import h3 as h3_lib
                invalid_h3 = gdf['h3_index'].apply(
                    lambda x: not isinstance(x, str) or not h3_lib.is_valid_cell(x)
                )
                if invalid_h3.any():
                    validation_result['issues'].append('Invalid H3 index format detected')

            validation_result['is_valid'] = len(validation_result['issues']) == 0

        except Exception as e:
            validation_result['issues'].append(f'Validation error: {str(e)}')

        return validation_result
