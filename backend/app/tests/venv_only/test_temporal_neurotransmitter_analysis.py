"""
venv_only test for Temporal Neurotransmitter Analysis.

This test requires pandas and numpy packages but no external services.
It demonstrates analyzing temporal patterns in neurotransmitter levels
for psychiatric digital twin models.
"""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Any, Optional, Union
from unittest.mock import MagicMock


# ================= Model Classes =================

class NeurotransmitterType(str, Enum):
    """Types of neurotransmitters being analyzed."""
    SEROTONIN = "serotonin"
    DOPAMINE = "dopamine"
    GABA = "gaba"
    GLUTAMATE = "glutamate"
    NOREPINEPHRINE = "norepinephrine"
    ACETYLCHOLINE = "acetylcholine"
    ENDORPHIN = "endorphin"
OXYTOCIN = "oxytocin"


class TemporalPatternType(str, Enum):
    """Types of temporal patterns that can be identified."""
    DAILY_CYCLE = "daily_cycle"
    WEEKLY_CYCLE = "weekly_cycle"
    GRADUAL_INCREASE = "gradual_increase"
    GRADUAL_DECREASE = "gradual_decrease"
    SUDDEN_SPIKE = "sudden_spike"
    SUDDEN_DROP = "sudden_drop"
    STABLE = "stable"
IRREGULAR = "irregular"
    CUSTOM = "custom"


class NeurotransmitterReading:
    """A single reading of a neurotransmitter level."""
    
    def __init__(
        self,
        neurotransmitter: NeurotransmitterType,
        level: float,
        timestamp: datetime,
        patient_id: str,
        source: str = "simulated",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a neurotransmitter reading.
        
        Args:
            neurotransmitter: Type of neurotransmitter
            level: Measured level (normalized 0-100)
            timestamp: When the reading was taken
            patient_id: ID of the patient
            source: Source of the reading (e.g., "lab", "simulated")
            metadata: Additional metadata about the reading
        """
        self.neurotransmitter = neurotransmitter
        self.level = level
        self.timestamp = timestamp
        self.patient_id = patient_id
        self.source = source
        self.metadata = metadata or {}
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "neurotransmitter": self.neurotransmitter.value,
            "level": self.level,
            "timestamp": self.timestamp.isoformat(),
            "patient_id": self.patient_id,
            "@pytest.mark.standalone
source": self.source,
            "metadata": self.metadata
        }


class TemporalNeurotransmitterAnalyzer:
    """Analyzer for temporal patterns in neurotransmitter levels."""
    
    def __init__(self, patient_id: str):
        """
        Initialize the analyzer.
        
        Args:
            patient_id: ID of the patient
        """
        self.patient_id = patient_id
        self.readings: Dict[NeurotransmitterType, List[NeurotransmitterReading]] = {
            nt_type: [] for nt_type in NeurotransmitterType
        }
        
    def add_reading(self, reading: NeurotransmitterReading) -> None:
        """
        Add a neurotransmitter reading.
        
        Args:
            reading: The reading to add
        """
        if reading.patient_id != self.patient_id:
            raise ValueError("Reading patient ID does not match analyzer patient ID")
            
        self.readings[reading.neurotransmitter].append(reading)
        
    def add_readings(self, readings: List[NeurotransmitterReading]) -> None:
        """
        Add multiple neurotransmitter readings.
        
        Args:
            readings: The readings to add
        """
        for reading in readings:
            self.add_reading(reading)
            
    def get_dataframe(self, neurotransmitter: NeurotransmitterType) -> pd.DataFrame:
        """
        Get a pandas DataFrame of readings for a neurotransmitter.
        
        Args:
            neurotransmitter: The neurotransmitter to get readings for
            
        Returns:
            DataFrame with columns: timestamp, level
        """
        readings = self.readings[neurotransmitter]
        
        if not readings:
            # Return empty DataFrame with correct columns
            return pd.DataFrame(columns=["timestamp", "level"])
            
        # Create DataFrame
        data = {
            "timestamp": [r.timestamp for r in readings],
            "level": [r.level for r in readings]
        }
        
        df = pd.DataFrame(data)
        
        # Sort by timestamp
        df = df.sort_values("timestamp")
        
        # Set timestamp as index
        df = df.set_index("timestamp")
        
        return df
        
    def analyze_pattern(
        self, 
        neurotransmitter: NeurotransmitterType,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze the temporal pattern of a neurotransmitter.
        
        Args:
            neurotransmitter: The neurotransmitter to analyze
            timeframe_days: Number of past days to analyze
            
        Returns:
            Analysis results including pattern type, statistics, etc.
        """
        # Get DataFrame for this neurotransmitter
        df = self.get_dataframe(neurotransmitter)
        
        if df.empty:
            return {
                "pattern_type": None,
                "confidence": 0.0,
                "mean": None,
                "std": None,
                "min": None,
                "max": None,
                "trend": None,
                "has_daily_cycle": False,
                "has_weekly_cycle": False,
                "patient_id": self.patient_id,
                "neurotransmitter": neurotransmitter.value,
                "timeframe_days": timeframe_days,
                "data_points": 0
            }
            
        # Filter for the timeframe
        cutoff_date = datetime.now() - timedelta(days=timeframe_days)
        df = df[df.index >= cutoff_date]
        
        if df.empty:
            return {
                "pattern_type": None,
                "confidence": 0.0,
                "mean": None,
                "std": None,
                "min": None,
                "max": None,
                "trend": None,
                "has_daily_cycle": False,
                "has_weekly_cycle": False,
                "patient_id": self.patient_id,
                "neurotransmitter": neurotransmitter.value,
                "timeframe_days": timeframe_days,
                "data_points": 0
            }
            
        # Basic statistics
        mean_level = df["level"].mean()
        std_level = df["level"].std()
        min_level = df["level"].min()
        max_level = df["level"].max()
        
        # Detect trend (using simple linear regression)
        df = df.reset_index()
        df["days"] = (df["timestamp"] - df["timestamp"].min()).dt.total_seconds() / (24 * 3600)
        
        if len(df) >= 2:
            # Use numpy for linear regression
            slope, _ = np.polyfit(df["days"], df["level"], 1)
            
            # Determine trend direction
            if abs(slope) < 0.1:  # Very small slope
                trend = "stable"
            elif slope > 0:
                trend = "increasing"
            else:
                trend = "decreasing"
        else:
            trend = "unknown"
            slope = 0
            
        # Check for daily cycles
        has_daily_cycle = False
        daily_cycle_confidence = 0.0
        
        if len(df) >= 24:  # Need at least 24 hours of data
            # Group by hour of day
            df["hour"] = df["timestamp"].dt.hour
            hourly_means = df.groupby("hour")["level"].mean()
            
            # Check if there's significant variation by hour
            hourly_std = hourly_means.std()
            if hourly_std > 5.0:  # Arbitrary threshold
                has_daily_cycle = True
                daily_cycle_confidence = min(1.0, hourly_std / 10.0)  # Scale to 0-1
        
        # Check for weekly cycles
        has_weekly_cycle = False
        weekly_cycle_confidence = 0.0
        
        if len(df) >= 7 * 24:  # Need at least a week of data
            # Group by day of week
            df["day_of_week"] = df["timestamp"].dt.dayofweek
            daily_means = df.groupby("day_of_week")["level"].mean()
            
            # Check if there's significant variation by day
            daily_std = daily_means.std()
            if daily_std > 7.0:  # Arbitrary threshold
                has_weekly_cycle = True
                weekly_cycle_confidence = min(1.0, daily_std / 14.0)  # Scale to 0-1
        
        # Determine overall pattern type
        if has_daily_cycle and daily_cycle_confidence > 0.6:
            pattern_type = TemporalPatternType.DAILY_CYCLE
            confidence = daily_cycle_confidence
        elif has_weekly_cycle and weekly_cycle_confidence > 0.6:
            pattern_type = TemporalPatternType.WEEKLY_CYCLE
            confidence = weekly_cycle_confidence
        elif trend == "increasing" and abs(slope) > 0.5:
            pattern_type = TemporalPatternType.GRADUAL_INCREASE
            confidence = min(1.0, abs(slope) / 2.0)
        elif trend == "decreasing" and abs(slope) > 0.5:
            pattern_type = TemporalPatternType.GRADUAL_DECREASE
            confidence = min(1.0, abs(slope) / 2.0)
        elif std_level < 5.0 and len(df) >= 10:
            pattern_type = TemporalPatternType.STABLE
            confidence = min(1.0, 10.0 / std_level) if std_level > 0 else 0.95
        else:
            pattern_type = TemporalPatternType.IRREGULAR
            confidence = 0.7
            
        # Create result dictionary
        result = {
            "pattern_type": pattern_type.value,
            "confidence": confidence,
            "mean": mean_level,
            "std": std_level,
            "min": min_level,
            "max": max_level,
            "trend": trend,
            "trend_slope": slope,
            "has_daily_cycle": has_daily_cycle,
            "daily_cycle_confidence": daily_cycle_confidence,
            "has_weekly_cycle": has_weekly_cycle,
            "weekly_cycle_confidence": weekly_cycle_confidence,
            "patient_id": self.patient_id,
            "neurotransmitter": neurotransmitter.value,
            "timeframe_days": timeframe_days,
            "data_points": len(df)
        }
        
        return result
        
    def analyze_all(self, timeframe_days: int = 30) -> Dict[str, Dict[str, Any]]:
        """
        Analyze patterns for all neurotransmitters.
        
        Args:
            timeframe_days: Number of past days to analyze
            
        Returns:
            Dictionary mapping neurotransmitter names to analysis results
        """
        results = {}
        
        for nt_type in NeurotransmitterType:
            if not self.readings[nt_type]:
                continue
                
            results[nt_type.value] = self.analyze_pattern(nt_type, timeframe_days)
            
        return results
        
    def generate_synthetic_data(
        self,
        neurotransmitter: NeurotransmitterType,
        pattern: TemporalPatternType,
        days: int = 30,
        readings_per_day: int = 24,
        base_level: float = 50.0,
        variation: float = 10.0
    ) -> List[NeurotransmitterReading]:
        """
        Generate synthetic data with a specific pattern.
        
        Args:
            neurotransmitter: The neurotransmitter to generate data for
            pattern: The pattern to generate
            days: Number of days of data to generate
            readings_per_day: Number of readings per day
            base_level: Base neurotransmitter level
            variation: Amount of random variation
            
        Returns:
            List of synthetic neurotransmitter readings
        """
        readings = []
        
        # Generate timestamps
        end_time = datetime.now()
        start_time = end_time - timedelta(days=days)
        
        # Calculate time step
        total_readings = days * readings_per_day
        time_step = (end_time - start_time) / total_readings
        
        # Generate readings based on pattern
        for i in range(total_readings):
            timestamp = start_time + time_step * i
            
            # Base level with noise
            level = base_level + np.random.normal(0, variation / 3)
            
            # Apply pattern
            if pattern == TemporalPatternType.DAILY_CYCLE:
                # Add daily cycle: highest in morning, lowest at night
                hour = timestamp.hour
                daily_factor = np.sin(hour / 24 * 2 * np.pi)
                level += daily_factor * variation
                
            elif pattern == TemporalPatternType.WEEKLY_CYCLE:
                # Add weekly cycle: higher on weekends
                day_of_week = timestamp.weekday()
                weekend_factor = 1.0 if day_of_week >= 5 else 0.0  # Weekend boost
                level += weekend_factor * variation
                
            elif pattern == TemporalPatternType.GRADUAL_INCREASE:
                # Gradual increase over time
                progress = i / total_readings
                level += progress * variation * 2
                
            elif pattern == TemporalPatternType.GRADUAL_DECREASE:
                # Gradual decrease over time
                progress = i / total_readings
                level -= progress * variation * 2
                
            elif pattern == TemporalPatternType.SUDDEN_SPIKE:
                # Occasional spikes
                if np.random.random() < 0.05:  # 5% chance of spike
                    level += variation * 2
                    
            elif pattern == TemporalPatternType.SUDDEN_DROP:
                # Occasional drops
                if np.random.random() < 0.05:  # 5% chance of drop
                    level -= variation * 2
                    
            elif pattern == TemporalPatternType.STABLE:
                # Just the base level with minimal noise
                level = base_level + np.random.normal(0, variation / 10)
                
            elif pattern == TemporalPatternType.IRREGULAR:
                # Add more noise and some random spikes and drops
                level += np.random.normal(0, variation)
                if np.random.random() < 0.1:  # 10% chance of spike or drop
                    level += np.random.choice([-1, 1]) * variation * 1.5
            
            # Ensure level is within reasonable bounds
            level = max(0, min(100, level))
            
            # Create reading
            reading = NeurotransmitterReading(
                neurotransmitter=neurotransmitter,
                level=level,
                timestamp=timestamp,
                patient_id=self.patient_id,
                source="synthetic",
                metadata={"pattern": pattern.value}
            )
            
            readings.append(reading)
            
        return readings

    def get_pattern_correlation(
        self, 
        neurotransmitter1: NeurotransmitterType,
        neurotransmitter2: NeurotransmitterType,
        timeframe_days: int = 30
    ) -> Dict[str, Any]:
        """
        Analyze correlations between two neurotransmitters over time.
        
        Args:
            neurotransmitter1: First neurotransmitter
            neurotransmitter2: Second neurotransmitter
            timeframe_days: Number of past days to analyze
            
        Returns:
            Correlation analysis results
        """
        # Get DataFrames
        df1 = self.get_dataframe(neurotransmitter1)
        df2 = self.get_dataframe(neurotransmitter2)
        
        if df1.empty or df2.empty:
            return {
                "correlation": 0,
                "p_value": 1.0,
                "synchronized": False,
                "relationship": "unknown",
                "lag_hours": 0,
                "data_points": 0
            }
            
        # Filter for timeframe
        cutoff_date = datetime.now() - timedelta(days=timeframe_days)
        df1 = df1[df1.index >= cutoff_date]
        df2 = df2[df2.index >= cutoff_date]
        
        if df1.empty or df2.empty:
            return {
                "correlation": 0,
                "p_value": 1.0, 
                "synchronized": False,
                "relationship": "unknown",
                "lag_hours": 0,
                "data_points": 0
            }
            
        # Resample to hourly data for proper comparison
        df1_hourly = df1.reset_index()
        df1_hourly["hour"] = df1_hourly["timestamp"].dt.floor("H")
        df1_hourly = df1_hourly.groupby("hour").mean()
        
        df2_hourly = df2.reset_index()
        df2_hourly["hour"] = df2_hourly["timestamp"].dt.floor("H")
        df2_hourly = df2_hourly.groupby("hour").mean()
        
        # Merge dataframes
        df_merged = pd.merge(
            df1_hourly, 
            df2_hourly,
            left_index=True,
            right_index=True,
            suffixes=(f"_{neurotransmitter1.value}", f"_{neurotransmitter2.value}")
        )
        
        if df_merged.empty or len(df_merged) < 3:  # Need at least 3 points for correlation
            return {
                "correlation": 0,
                "p_value": 1.0,
                "synchronized": False,
                "relationship": "unknown",
                "lag_hours": 0,
                "data_points": len(df_merged)
            }
            
        # Calculate correlation
        correlation = np.corrcoef(
            df_merged[f"level_{neurotransmitter1.value}"],
            df_merged[f"level_{neurotransmitter2.value}"]
        )[0, 1]
        
        # Simple p-value estimation based on sample size
        # In a real implementation, this would use scipy.stats
        n = len(df_merged)
        t = abs(correlation) * np.sqrt(n - 2) / np.sqrt(1 - correlation**2)
        p_value = 2 * (1 - min(0.9999, t / np.sqrt(n)))  # Simplified p-value calculation
        
        # Determine relationship
        if abs(correlation) < 0.3:
            relationship = "unrelated"
            synchronized = False
        elif correlation >= 0.3:
            relationship = "positively_correlated"
            synchronized = True
        else:
            relationship = "negatively_correlated"
            synchronized = True
            
        # In a real implementation, we would calculate lag using cross-correlation
        # Here we'll just use a random value for demonstration
        lag_hours = 0
        
        # Create result
        result = {
            "correlation": correlation,
            "p_value": p_value,
            "synchronized": synchronized,
            "relationship": relationship,
            "lag_hours": lag_hours,
            "neurotransmitter1": neurotransmitter1.value,
            "neurotransmitter2": neurotransmitter2.value,
            "timeframe_days": timeframe_days,
            "data_points": len(df_merged)
        }
   
        return result


# ================= Tests =================

def test_neurotransmitter_analyzer_pattern_detection():
    """Test that the analyzer can detect different temporal patterns."""
    # Set up analyzer
    analyzer = TemporalNeurotransmitterAnalyzer(patient_id="test_patient")
    
    # Test different patterns
    patterns_to_test = [
        TemporalPatternType.DAILY_CYCLE,
        TemporalPatternType.WEEKLY_CYCLE,
        TemporalPatternType.GRADUAL_INCREASE,
        TemporalPatternType.GRADUAL_DECREASE,
        TemporalPatternType.STABLE
    ]
    
    for i, pattern in enumerate(patterns_to_test):
        # Generate synthetic data with this pattern
        nt_type = list(NeurotransmitterType)[i % len(NeurotransmitterType)]
        
        readings = analyzer.generate_synthetic_data(
            neurotransmitter=nt_type,
            pattern=pattern,
            days=30,
            readings_per_day=24
        )
        
        # Add the readings to the analyzer
        analyzer.add_readings(readings)
        
        # Analyze the pattern
        result = analyzer.analyze_pattern(nt_type)
        
        # Check that the pattern was correctly detected
        assert result["pattern_type"] == pattern.value, \
            f"Expected {pattern.value}, got {result['pattern_type']}"
        assert result["confidence"] > 0.5, \
f"Confidence too low: {result['confidence']}"
        assert result["data_points"] > 0
        

def test_neurotransmitter_analyzer_with_pandas():
    """Test that the analyzer correctly uses pandas for data analysis."""
    # Set up analyzer
    analyzer = TemporalNeurotransmitterAnalyzer(patient_id="test_patient")
    
    # Generate some test data
    days = 30
    readings_per_day = 24
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    time_step = timedelta(days=1) / readings_per_day
    
    readings = []
    for i in range(days * readings_per_day):
        timestamp = start_time + time_step * i
        # Create a sine wave pattern
        level = 50 + 20 * np.sin(i / 24 * 2 * np.pi)
        
        reading = NeurotransmitterReading(
            neurotransmitter=NeurotransmitterType.SEROTONIN,
            level=level,
            timestamp=timestamp,
            patient_id="test_patient"
        )
        readings.append(reading)
    
    # Add readings to analyzer
    analyzer.add_readings(readings)
    
    # Get DataFrame
    df = analyzer.get_dataframe(NeurotransmitterType.SEROTONIN)
    
    # Check that we got a DataFrame with the expected properties
    assert isinstance(df, pd.DataFrame)
    assert len(df) == days * readings_per_day
    assert "level" in df.columns
    
    # Check that the index is a DatetimeIndex
    assert isinstance(df.index, pd.DatetimeIndex)
    
    # Analyze the pattern
    result = analyzer.analyze_pattern(NeurotransmitterType.SEROTONIN)
    
    # The sine wave should be detected as a daily cycle
    assert result["pattern_type"] == TemporalPatternType.DAI@pytest.mark.standalone
LY_CYCLE.value
    assert result["has_daily_cycle"] == True
    assert "mean" in result
    assert "std" in result
    

def test_neurotransmitter_correlation_analysis():
    """Test that correlations between neurotransmitters can be analyzed."""
    # Set up analyzer
    analyzer = TemporalNeurotransmitterAnalyzer(patient_id="test_patient")
    
    # Generate positively correlated data
    days = 10
    readings_per_day = 24
    end_time = datetime.now()
    start_time = end_time - timedelta(days=days)
    time_step = timedelta(days=1) / readings_per_day
    
    serotonin_readings = []
    dopamine_readings = []
    
    # Generate correlated data: dopamine follows serotonin with some noise
    for i in range(days * readings_per_day):
        timestamp = start_time + time_step * i
        
        # Base pattern is a sine wave
        base = np.sin(i / 24 * 2 * np.pi)
        
        # Serotonin follows the pattern with some noise
        serotonin = 50 + 20 * base + np.random.normal(0, 3)
        serotonin = max(0, min(100, serotonin))
        
        # Dopamine follows serotonin with additional noise
        dopamine = 40 + 0.7 * (serotonin - 50) + np.random.normal(0, 5)
        dopamine = max(0, min(100, dopamine))
        
        serotonin_readings.append(NeurotransmitterReading(
            neurotransmitter=NeurotransmitterType.SEROTONIN,
            level=serotonin,
            timestamp=timestamp,
            patient_id="test_patient"
        ))
        
        dopamine_readings.append(NeurotransmitterReading(
            neurotransmitter=NeurotransmitterType.DOPAMINE,
            level=dopamine,
            timestamp=timestamp,
            patient_id="test_patient"
        ))
    
    # Add readings to analyzer
    analyzer.add_readings(serotonin_readings)
    analyzer.add_readings(dopamine_readings)
    
    # Analyze correlation
    result = analyzer.get_pattern_correlation(
        NeurotransmitterType.SEROTONIN,
        NeurotransmitterType.DOPAMINE
    )
    
    # Check results
    assert "correlation" in result
    assert abs(result["correlation"]) >@pytest.mark.standalone
 0.5, "Expected strong correlation"
    assert result["relationship"] == "positively_correlated"
    assert result["synchronized"] == True
    

def test_synthetic_data_generation():
    """Test that synthetic data generation creates the expected patterns."""
    # Set up analyzer
    analyzer = TemporalNeurotransmitterAnalyzer(patient_id="test_patient")
    
    # Generate data with a daily cycle
    readings = analyzer.generate_synthetic_data(
        neurotransmitter=NeurotransmitterType.SEROTONIN,
        pattern=TemporalPatternType.DAILY_CYCLE,
        days=7,
        readings_per_day=24
    )
    
    # Check the readings
    assert len(readings) == 7 * 24
    assert all(r.neurotransmitter == NeurotransmitterType.SEROTONIN for r in readings)
    assert all(r.patient_id == "test_patient" for r in readings)
    assert all(0 <= r.level <= 100 for r in readings)
    
    # Add the readings and analyze
    analyzer.add_readings(readings)
    result = analyzer.analyze_pattern(NeurotransmitterType.SEROTONIN)
    
    # Since we gene@pytest.mark.standalone
rated a daily cycle, it should be detected
    assert result["has_daily_cycle"] == True
    assert result["pattern_type"] == TemporalPatternType.DAILY_CYCLE.value
    

def test_analyze_all_neurotransmitters():
    """Test analyzing all neurotransmitters at once."""
    # Set up analyzer
    analyzer = TemporalNeurotransmitterAnalyzer(patient_id="test_patient")
    
    # Generate data for several neurotransmitters with different patterns
    patterns = {
        NeurotransmitterType.SEROTONIN: TemporalPatternType.DAILY_CYCLE,
        NeurotransmitterType.DOPAMINE: TemporalPatternType.GRADUAL_INCREASE,
        NeurotransmitterType.GABA: TemporalPatternType.STABLE
    }
    
    for nt_type, pattern in patterns.items():
        readings = analyzer.generate_synthetic_data(
            neurotransmitter=nt_type,
            pattern=pattern,
            days=10,
            readings_per_day=24
        )
        analyzer.add_readings(readings)
    
    # Analyze all
    results = analyzer.analyze_all(timeframe_days=10)
    
    # Check results
    assert len(results) == len(patterns)
    for nt_type, pattern in patterns.items():
        assert nt_type.value in results
        assert results[nt_type.value]["pattern_type"] == pattern.value
        assert results[nt_type.value]["data_points"] > 0