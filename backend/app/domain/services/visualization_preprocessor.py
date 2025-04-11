"""
Domain service for preprocessing neurotransmitter data for visualization.

This module contains preprocessing logic to optimize neurotransmitter data
for efficient visualization in the frontend.
"""
import math
from typing import Any

from app.domain.entities.digital_twin_enums import (
    BrainRegion,
    ClinicalSignificance,
    Neurotransmitter,
)
from app.domain.entities.neurotransmitter_effect import NeurotransmitterEffect
from app.domain.entities.temporal_sequence import TemporalSequence


class NeurotransmitterVisualizationPreprocessor:
    """
    Handles preprocessing of neurotransmitter data for visualization.
    
    This class optimizes and transforms temporal sequences and neurotransmitter
    data to formats more conducive to efficient visualization in the frontend.
    It includes methods for downsampling, geometry generation, and statistical
    preprocessing to ensure smooth rendering even with large datasets.
    """
    
    def __init__(self):
        """Initialize the preprocessor with required brain region coordinates."""
        # Define standardized 3D coordinates for each brain region
        # These are normalized coordinates that can be used by visualization engines
        self._brain_region_coordinates = {
            BrainRegion.PREFRONTAL_CORTEX: (0.0, 0.8, 0.3),
            BrainRegion.ORBITOFRONTAL_CORTEX: (0.0, 0.7, 0.1),
            BrainRegion.ANTERIOR_CINGULATE_CORTEX: (0.0, 0.5, 0.4),
            BrainRegion.AMYGDALA: (0.3, 0.1, 0.0),
            BrainRegion.HIPPOCAMPUS: (0.4, 0.0, 0.2),
            BrainRegion.INSULA: (0.5, 0.3, 0.1),
            BrainRegion.NUCLEUS_ACCUMBENS: (0.2, 0.3, -0.1),
            BrainRegion.VENTRAL_TEGMENTAL_AREA: (0.0, -0.3, 0.0),
            BrainRegion.SUBSTANTIA_NIGRA: (0.1, -0.5, -0.1),
            BrainRegion.LOCUS_COERULEUS: (-0.1, -0.7, 0.0),
            BrainRegion.RAPHE_NUCLEI: (0.0, -0.6, 0.2),
            BrainRegion.HYPOTHALAMUS: (0.0, 0.0, -0.2),
            BrainRegion.THALAMUS: (0.0, 0.1, 0.0),
            BrainRegion.STRIATUM: (0.3, 0.2, 0.0),
            BrainRegion.PARIETAL_CORTEX: (0.4, 0.5, 0.6),
            BrainRegion.TEMPORAL_CORTEX: (0.6, 0.3, 0.3),
            BrainRegion.OCCIPITAL_CORTEX: (0.5, -0.3, 0.5),
            BrainRegion.CEREBELLUM: (0.0, -0.8, 0.4),
            BrainRegion.BRAIN_STEM: (0.0, -0.9, 0.0),
            BrainRegion.BASAL_GANGLIA: (0.2, 0.1, 0.0),
            BrainRegion.VENTRAL_STRIATUM: (0.25, 0.15, -0.05),
            BrainRegion.DORSAL_STRIATUM: (0.3, 0.25, 0.05)
        }
        
        # Color mappings for neurotransmitters - used for visualization
        self._neurotransmitter_colors = {
            Neurotransmitter.SEROTONIN: (0.8, 0.2, 0.8),  # Purple
            Neurotransmitter.DOPAMINE: (0.2, 0.8, 0.2),   # Green
            Neurotransmitter.NOREPINEPHRINE: (0.2, 0.2, 0.8),  # Blue
            Neurotransmitter.GABA: (0.8, 0.6, 0.2),       # Orange
            Neurotransmitter.GLUTAMATE: (0.8, 0.2, 0.2),  # Red
            Neurotransmitter.ACETYLCHOLINE: (0.6, 0.8, 0.8),  # Light Blue
            Neurotransmitter.ENDORPHINS: (0.9, 0.7, 0.9),  # Light Purple
            Neurotransmitter.SUBSTANCE_P: (0.7, 0.3, 0.1),  # Brown
            Neurotransmitter.OXYTOCIN: (0.9, 0.4, 0.6),  # Pink
            Neurotransmitter.HISTAMINE: (0.5, 0.5, 0.1),  # Olive
            Neurotransmitter.GLYCINE: (0.4, 0.8, 0.4),  # Light Green
            Neurotransmitter.ADENOSINE: (0.6, 0.6, 0.6)   # Gray
        }
    
    def precompute_temporal_sequence_visualization(
        self,
        sequence: TemporalSequence,
        focus_features: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Precompute visualization data for a temporal sequence.
        
        Args:
            sequence: The temporal sequence to visualize
            focus_features: Optional list of features to focus on
            
        Returns:
            Dictionary with preprocessed visualization data
        """
        # Determine which features to include
        features = focus_features or sequence.feature_names
        
        # Get time and value data
        timestamps = sequence.timestamps
        
        # Determine if downsampling is needed
        downsample = len(timestamps) > 100
        sample_rate = max(1, len(timestamps) // 100) if downsample else 1
        
        # Create downsampled data points
        downsampled_times = []
        downsampled_values = []
        
        for i in range(0, len(timestamps), sample_rate):
            downsampled_times.append(timestamps[i])
            
            # Get feature values for this timestamp
            feature_values = {}
            for feature in features:
                if feature in sequence.feature_names:
                    feature_idx = sequence.feature_names.index(feature)
                    if i < len(sequence.values) and feature_idx < len(sequence.values[i]):
                        feature_values[feature] = sequence.values[i][feature_idx]
                    else:
                        feature_values[feature] = 0.0  # Default if out of range
                else:
                    feature_values[feature] = 0.0  # Default if feature not in sequence
                    
            downsampled_values.append(feature_values)
        
        # Calculate statistics for visualization aids
        feature_stats = {}
        for feature in features:
            values = [point.get(feature, 0.0) for point in downsampled_values]
            if values:
                feature_stats[feature] = {
                    "min": min(values),
                    "max": max(values),
                    "avg": sum(values) / len(values),
                    "trend": self._calculate_trend(values)
                }
        
        # Generate color and opacity mappings
        colors = {}
        for feature in features:
            if feature in [nt.value for nt in Neurotransmitter]:
                # Try to find matching neurotransmitter
                for nt in Neurotransmitter:
                    if nt.value == feature:
                        colors[feature] = {
                            "rgb": self._neurotransmitter_colors.get(nt, (0.5, 0.5, 0.5)),
                            "hex": self._rgb_to_hex(self._neurotransmitter_colors.get(nt, (0.5, 0.5, 0.5)))
                        }
                        break
            else:
                # Generate color algorithmically
                hue = hash(feature) % 360 / 360.0
                colors[feature] = {
                    "rgb": self._hsv_to_rgb(hue, 0.7, 0.8),
                    "hex": self._rgb_to_hex(self._hsv_to_rgb(hue, 0.7, 0.8))
                }
        
        # Return visualization-ready data
        return {
            "downsampled": downsample,
            "sample_rate": sample_rate,
            "times": [t.isoformat() for t in downsampled_times],
            "values": downsampled_values,
            "features": features,
            "feature_stats": feature_stats,
            "colors": colors,
            "brain_region": sequence.brain_region.value if sequence.brain_region else None,
            "neurotransmitter": sequence.neurotransmitter.value if sequence.neurotransmitter else None
        }
    
    def precompute_cascade_geometry(
        self,
        cascade_data: dict[BrainRegion, list[float]]
    ) -> dict[str, Any]:
        """
        Generate geometry data for neurotransmitter cascade visualization.
        
        Args:
            cascade_data: Dictionary mapping brain regions to activity values over time
            
        Returns:
            Dictionary with preprocessed visualization data
        """
        # Extract time steps from data
        time_steps = 0
        for region, values in cascade_data.items():
            time_steps = max(time_steps, len(values))
        
        # Generate vertices, colors, and connections for each time step
        vertices_by_time = []
        colors_by_time = []
        
        for t in range(time_steps):
            vertices = []
            colors = []
            
            # Process each brain region
            for region, values in cascade_data.items():
                if t < len(values):
                    # Get activity value for this region at this time
                    activity = values[t]
                    
                    # Skip if activity is negligible
                    if activity < 0.05:
                        continue
                    
                    # Get coordinates for this region
                    coords = self._brain_region_coordinates.get(region, (0, 0, 0))
                    
                    # Add coordinates to vertices
                    vertices.extend([coords[0], coords[1], coords[2]])
                    
                    # Scale color intensity by activity
                    color = (0.2 + 0.8 * activity, 0.2, 0.8 * activity)
                    colors.extend(color)
            
            # Add to time-based collections
            vertices_by_time.append(vertices)
            colors_by_time.append(colors)
        
        # Generate connections between active regions
        connections = []
        active_regions = set(cascade_data.keys())
        
        for region1 in active_regions:
            for region2 in active_regions:
                if region1 != region2:
                    # Calculate if there's a temporal connection
                    region1_data = cascade_data.get(region1, [])
                    region2_data = cascade_data.get(region2, [])
                    
                    # Find first time each region becomes active
                    region1_active_at = next((i for i, v in enumerate(region1_data) if v > 0.1), -1)
                    region2_active_at = next((i for i, v in enumerate(region2_data) if v > 0.1), -1)
                    
                    # Connection exists if region2 activates shortly after region1
                    if 0 <= region1_active_at < region2_active_at <= region1_active_at + 3:
                        # Get coordinates for both regions
                        coords1 = self._brain_region_coordinates.get(region1, (0, 0, 0))
                        coords2 = self._brain_region_coordinates.get(region2, (0, 0, 0))
                        
                        # Create connection
                        connection = {
                            "from": region1.value,
                            "to": region2.value,
                            "from_coords": coords1,
                            "to_coords": coords2,
                            "lag": region2_active_at - region1_active_at,
                            "strength": 0.0
                        }
                        
                        # Calculate connection strength
                        for t in range(time_steps - 1):
                            if t < len(region1_data) and t+1 < len(region2_data):
                                if region1_data[t] > 0.1:
                                    # Measure region2's response to region1
                                    delta = region2_data[t+1] - region2_data[t]
                                    if delta > 0:
                                        connection["strength"] += delta * region1_data[t]
                        
                        # Only add meaningful connections
                        if connection["strength"] > 0.05:
                            connections.append(connection)
        
        # Return precomputed geometry data
        return {
            "vertices_by_time": vertices_by_time,
            "colors_by_time": colors_by_time,
            "connections": connections,
            "time_steps": time_steps,
            "active_regions": [region.value for region in active_regions]
        }
    
    def _calculate_trend(self, values: list[float]) -> str:
        """
        Calculate the trend direction of a series of values.
        
        Args:
            values: List of numeric values
            
        Returns:
            Trend description ("increasing", "decreasing", "stable", or "volatile")
        """
        if not values or len(values) < 2:
            return "insufficient_data"
        
        # Calculate first and last values
        start_value = values[0]
        end_value = values[-1]
        
        # Calculate percent change
        if start_value == 0:
            percent_change = float('inf') if end_value > 0 else 0
        else:
            percent_change = (end_value - start_value) / start_value * 100
        
        # Calculate volatility (standard deviation of changes)
        changes = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                changes.append((values[i] - values[i-1]) / values[i-1])
        
        volatility = 0
        if changes:
            mean = sum(changes) / len(changes)
            variance = sum((x - mean) ** 2 for x in changes) / len(changes)
            volatility = math.sqrt(variance)
        
        # Determine trend
        if volatility > 0.2:
            return "volatile"
        elif percent_change > 10:
            return "increasing"
        elif percent_change < -10:
            return "decreasing"
        else:
            return "stable"
    
    def _rgb_to_hex(self, rgb_tuple: tuple[float, float, float]) -> str:
        """
        Convert RGB tuple (0-1 range) to hex color string.
        
        Args:
            rgb_tuple: Tuple of (r, g, b) values in 0-1 range
            
        Returns:
            Hex color string (e.g., "#ff0000" for red)
        """
        r, g, b = rgb_tuple
        return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"
    
    def _hsv_to_rgb(self, h: float, s: float, v: float) -> tuple[float, float, float]:
        """
        Convert HSV colors to RGB.
        
        Args:
            h: Hue (0-1 range)
            s: Saturation (0-1 range)
            v: Value (0-1 range)
            
        Returns:
            Tuple of (r, g, b) values in 0-1 range
        """
        if s == 0.0:
            return (v, v, v)
        
        i = int(h * 6)
        f = (h * 6) - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))
        
        i %= 6
        
        if i == 0:
            return (v, t, p)
        if i == 1:
            return (q, v, p)
        if i == 2:
            return (p, v, t)
        if i == 3:
            return (p, q, v)
        if i == 4:
            return (t, p, v)
        return (v, p, q)  # i == 5


class NeurotransmitterEffectVisualizer:
    """
    Specialized visualizer for neurotransmitter effects.
    
    This class transforms NeurotransmitterEffect objects into formats optimized
    for visualization in the frontend, applying color mapping, intensity scaling,
    and generating visualization-ready data.
    """
    
    def __init__(self):
        """Initialize the visualizer with default color mappings."""
        # Define color mappings for different clinical significance levels
        self._significance_colors = {
            ClinicalSignificance.NONE: "#888888",      # Gray
            ClinicalSignificance.MINIMAL: "#aaccee",   # Light blue
            ClinicalSignificance.MILD: "#66aadd",      # Medium blue
            ClinicalSignificance.MODERATE: "#ee8822",  # Orange
            ClinicalSignificance.SIGNIFICANT: "#dd3311" # Red
        }
        
        # Initialize preprocessor for coordinates and base colors
        self.preprocessor = NeurotransmitterVisualizationPreprocessor()
    
    def generate_effect_visualization(
        self,
        effect: NeurotransmitterEffect
    ) -> dict[str, Any]:
        """
        Generate visualization data for a neurotransmitter effect.
        
        Args:
            effect: The neurotransmitter effect to visualize
            
        Returns:
            Dictionary with visualization-ready data
        """
        if not effect:
            return {"error": "No effect data provided"}
            
        # Get base color for this neurotransmitter
        base_color = "#888888"  # Default gray
        for nt, color in self.preprocessor._neurotransmitter_colors.items():
            if nt == effect.neurotransmitter:
                base_color = self.preprocessor._rgb_to_hex(color)
                break
        
        # Get significance color
        significance_color = self._significance_colors.get(
            effect.clinical_significance,
            self._significance_colors[ClinicalSignificance.NONE]
        )
        
        # Get brain region coordinates if available
        coordinates = None
        if effect.brain_region:
            coordinates = self.preprocessor._brain_region_coordinates.get(effect.brain_region)
        
        # Generate time series data if available
        time_series = None
        if effect.time_series_data:
            time_series = {
                "times": [t.isoformat() for t, _ in effect.time_series_data],
                "values": [value for _, value in effect.time_series_data],
                "trend": effect.get_trend_direction()
            }
            
        # Return visualization data
        return {
            "neurotransmitter": effect.neurotransmitter.value,
            "brain_region": effect.brain_region.value if effect.brain_region else None,
            "effect_size": effect.effect_size,
            "is_significant": effect.is_statistically_significant,
            "clinical_significance": effect.clinical_significance.value,
            "confidence_interval": {
                "lower": effect.confidence_interval[0],
                "upper": effect.confidence_interval[1]
            },
            "visualization": {
                "base_color": base_color,
                "significance_color": significance_color,
                "coordinates": coordinates,
                "time_series": time_series,
                "relative_change": effect.get_relative_change()
            }
        }
        
    def generate_comparative_visualization(
        self,
        effects: list[NeurotransmitterEffect]
    ) -> dict[str, Any]:
        """
        Generate visualization data for comparing multiple effects.
        
        Args:
            effects: List of neurotransmitter effects to compare
            
        Returns:
            Dictionary with comparative visualization data
        """
        if not effects:
            return {"effects": [], "summary": "No effects data provided"}
            
        # Generate individual visualizations
        effect_visualizations = []
        for effect in effects:
            effect_visualizations.append(self.generate_effect_visualization(effect))
            
        # Create summary data
        brain_regions = set()
        neurotransmitters = set()
        max_effect_size = 0
        significant_count = 0
        
        for effect in effects:
            if effect.brain_region:
                brain_regions.add(effect.brain_region)
            neurotransmitters.add(effect.neurotransmitter)
            max_effect_size = max(max_effect_size, effect.effect_size)
            if effect.is_statistically_significant:
                significant_count += 1
                
        # Return comparative data
        return {
            "effects": effect_visualizations,
            "summary": {
                "brain_regions": [br.value for br in brain_regions],
                "neurotransmitters": [nt.value for nt in neurotransmitters],
                "max_effect_size": max_effect_size,
                "significant_count": significant_count,
                "total_effects": len(effects)
            }
        }