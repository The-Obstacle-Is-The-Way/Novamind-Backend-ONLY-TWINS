"""
Unit tests for the Temporal Dynamics components of the Digital Twin.

This module contains tests for temporal pattern detection, trajectory prediction,
and longitudinal modeling capabilities of the Digital Twin system.
"""
import unittest
from datetime import datetime, timedelta
from uuid import uuid4

import numpy as np

from app.domain.entities.digital_twin.state import DigitalTwinState
from app.domain.entities.digital_twin.temporal import (
    EpisodicPatternDetector,
    PatternDetector,
    PatternStrength,
    SeasonalPatternDetector,
    TemporalDynamics,
    TimeSeriesForecaster,
    TrajectoryPrediction,
)


class TestTemporalDynamics(unittest.TestCase):
    """Tests for the TemporalDynamics entity."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a base temporal dynamics object
        self.temporal_dynamics = TemporalDynamics(
            pattern_detectors={
                "seasonal": SeasonalPatternDetector(),
                "episodic": EpisodicPatternDetector()
            },
            history_window_days=365,
            min_data_points=10
        )
        
        # Create patient ID
        self.patient_id = uuid4()
        
        # Create some test state data
        self.test_states = []
        base_date = datetime.utcnow() - timedelta(days=100)
        
        # Generate 10 state points with decreasing depression severity
        for i in range(10):
            state = DigitalTwinState()
            
            # Set properties in neurotransmitter state
            state.neurotransmitter.serotonin_level = -0.4 + (i * 0.05)
            state.neurotransmitter.dopamine_level = -0.3 + (i * 0.04)
            
            # Set properties in psychological state
            state.psychological.mood_valence = -0.5 + (i * 0.06)
            state.psychological.anxiety_level = 0.7 - (i * 0.04)
            
            # Set properties in behavioral state
            state.behavioral.sleep_quality = 0.3 + (i * 0.05)
            state.behavioral.activity_level = -0.4 + (i * 0.07)
            
            # Set properties in cognitive state
            state.cognitive.attention_level = 0.4 + (i * 0.03)
            state.cognitive.concentration = 0.3 + (i * 0.04)
            
            # Set timestamp
            state.timestamp = base_date + timedelta(days=i*10)
            
            # Update derived values
            state.update_derived_values()
            
            # Add to test states
            self.test_states.append(state)
    
    def test_init_default_values(self):
        """Test that default values are correctly initialized."""
        dynamics = TemporalDynamics()
        
        assert isinstance(dynamics.pattern_detectors, dict)
        assert dynamics.history_window_days == 365
        assert dynamics.min_data_points == 5
        assert dynamics.state_history == []
        assert dynamics.forecasting_models == {}
        assert dynamics.validation_metrics == {}
    
    def test_init_custom_values(self):
        """Test initialization with custom values."""
        custom_detectors = {
            "seasonal": SeasonalPatternDetector(
                detection_threshold=0.6, 
                minimum_cycles=2
            ),
            "episodic": EpisodicPatternDetector(
                detection_threshold=0.7,
                episode_duration_range=(7, 60)  # 1-8 weeks
            )
        }
        
        dynamics = TemporalDynamics(
            pattern_detectors=custom_detectors,
            history_window_days=180,
            min_data_points=15,
            max_forecast_days=90
        )
        
        assert dynamics.pattern_detectors == custom_detectors
        assert dynamics.history_window_days == 180
        assert dynamics.min_data_points == 15
        assert dynamics.max_forecast_days == 90
    
    def test_record_state_point(self):
        """Test recording state points in history."""
        # Initial state is empty
        assert len(self.temporal_dynamics.state_history) == 0
        
        # Record first state
        timestamp = datetime.utcnow() - timedelta(days=10)
        self.temporal_dynamics.record_state_point(
            self.test_states[0], 
            timestamp=timestamp
        )
        
        # Verify state was recorded
        assert len(self.temporal_dynamics.state_history) == 1
        assert self.temporal_dynamics.state_history[0].timestamp == timestamp
        assert self.temporal_dynamics.state_history[0].state == self.test_states[0]
        
        # Record more states
        for i in range(1, 5):
            timestamp = datetime.utcnow() - timedelta(days=10-i)
            self.temporal_dynamics.record_state_point(
                self.test_states[i], 
                timestamp=timestamp
            )
        
        # Verify all states were recorded
        assert len(self.temporal_dynamics.state_history) == 5
        
        # Verify states are ordered by timestamp
        for i in range(1, 5):
            assert self.temporal_dynamics.state_history[i].timestamp > \
                   self.temporal_dynamics.state_history[i-1].timestamp
    
    def test_detect_patterns(self):
        """Test detection of temporal patterns."""
        # Add all test states to history
        for state in self.test_states:
            self.temporal_dynamics.record_state_point(state)
        
        # Detect patterns
        patterns = self.temporal_dynamics.detect_patterns()
        
        # Verify pattern detection
        assert "seasonal" in patterns
        assert "episodic" in patterns
        assert isinstance(patterns["seasonal"], PatternStrength)
        assert isinstance(patterns["episodic"], PatternStrength)
        
        # Should detect a decreasing trend in depression
        assert patterns["seasonal"].strength >= 0
        assert patterns["seasonal"].confidence >= 0
        assert patterns["seasonal"].cycle_length is not None
        
        # Should detect episodic pattern
        assert patterns["episodic"].strength >= 0
        assert patterns["episodic"].confidence >= 0
        assert patterns["episodic"].episode_count is not None
    
    def test_forecast_trajectory(self):
        """Test forecasting of state trajectory."""
        # Add all test states to history
        for state in self.test_states:
            self.temporal_dynamics.record_state_point(state)
        
        # Create forecasting model
        self.temporal_dynamics.initialize_forecasters()
        
        # Forecast trajectory
        forecast = self.temporal_dynamics.forecast_trajectory(days=30)
        
        # Verify forecast
        assert isinstance(forecast, TrajectoryPrediction)
        assert len(forecast.time_points) > 0
        assert len(forecast.mood_values) == len(forecast.time_points)
        assert len(forecast.anxiety_values) == len(forecast.time_points)
        
        # Should predict continued improvement
        assert forecast.mood_values[-1] > forecast.mood_values[0]
        assert forecast.anxiety_values[-1] < forecast.anxiety_values[0]
        
        # Should have confidence intervals
        assert "mood" in forecast.confidence_intervals
        assert "anxiety" in forecast.confidence_intervals
        assert len(forecast.confidence_intervals["mood"]) == len(forecast.time_points)
    
    def test_predict_response(self):
        """Test prediction of treatment response."""
        # Add all test states to history
        for state in self.test_states:
            self.temporal_dynamics.record_state_point(state)
        
        # Initialize forecasting model
        self.temporal_dynamics.initialize_forecasters()
        
        # Create treatment effect dictionary
        treatment_effects = {
            "serotonin_level": 0.3,
            "mood_valence": 0.2,
            "anxiety_level": -0.3,
            "sleep_quality": 0.2
        }
        
        # Predict treatment response
        response_prediction = self.temporal_dynamics.predict_treatment_response(
            treatment_effects, 
            days=30
        )
        
        # Verify prediction
        assert "trajectory" in response_prediction
        assert "efficacy" in response_prediction
        assert "time_to_response" in response_prediction
        assert "time_to_remission" in response_prediction
        assert "remission_probability" in response_prediction
        assert "confidence" in response_prediction
        
        # Trajectory should be improving
        trajectory = response_prediction["trajectory"]
        assert trajectory.mood_values[-1] > trajectory.mood_values[0]
        assert trajectory.anxiety_values[-1] < trajectory.anxiety_values[0]
    
    def test_detect_seasonality(self):
        """Test detection of seasonal patterns."""
        # Create a seasonal pattern
        base_date = datetime.utcnow() - timedelta(days=365)
        seasonal_states = []
        
        # Generate a full year of states with winter depression pattern
        for i in range(36):  # 36 data points over a year (~ every 10 days)
            state = DigitalTwinState()
            
            # Calculate day of year (0-365)
            day_of_year = (i * 10) % 365
            
            # Simulate seasonal mood changes (worse in winter, better in summer)
            # Winter solstice is around day 355, summer solstice around day 172
            seasonal_factor = np.sin((day_of_year - 172) * 2 * np.pi / 365)
            
            # Mood is worse in winter (negative seasonal_factor)
            state.psychological.mood_valence = -0.3 + (0.4 * -seasonal_factor)
            state.psychological.anxiety_level = 0.4 + (0.3 * seasonal_factor)
            
            # Sleep is worse in summer
            state.behavioral.sleep_quality = 0.5 + (0.2 * seasonal_factor)
            
            # Set timestamp
            state.timestamp = base_date + timedelta(days=i*10)
            
            # Update derived values
            state.update_derived_values()
            
            # Add to seasonal states
            seasonal_states.append(state)
        
        # Create temporal dynamics with seasonal states
        seasonal_dynamics = TemporalDynamics(
            pattern_detectors={
                "seasonal": SeasonalPatternDetector(detection_threshold=0.3)
            }
        )
        
        # Add all seasonal states
        for state in seasonal_states:
            seasonal_dynamics.record_state_point(state)
        
        # Detect patterns
        patterns = seasonal_dynamics.detect_patterns()
        
        # Verify seasonality was detected
        assert "seasonal" in patterns
        assert patterns["seasonal"].strength > 0.4
        assert patterns["seasonal"].confidence > 0.5
        assert 350 <= patterns["seasonal"].cycle_length <= 380  # Should be close to 365 days
    
    def test_detect_episodes(self):
        """Test detection of episodic patterns."""
        # Create an episodic pattern
        base_date = datetime.utcnow() - timedelta(days=365)
        episodic_states = []
        
        # Generate a year of states with 3 depressive episodes
        episode_starts = [30, 150, 270]  # Days when episodes start
        episode_length = 20  # Days
        
        # Generate data points every 5 days
        for i in range(73):  # 365/5 data points over a year
            state = DigitalTwinState()
            day = i * 5
            
            # Check if in an episode
            in_episode = False
            for start in episode_starts:
                if start <= day < start + episode_length:
                    in_episode = True
                    break
            
            # Set values based on episode status
            if in_episode:
                # In depressive episode
                state.psychological.mood_valence = -0.6
                state.psychological.anxiety_level = 0.7
                state.behavioral.sleep_quality = 0.2
                state.behavioral.activity_level = -0.5
            else:
                # Normal state
                state.psychological.mood_valence = 0.2
                state.psychological.anxiety_level = 0.3
                state.behavioral.sleep_quality = 0.7
                state.behavioral.activity_level = 0.3
            
            # Set timestamp
            state.timestamp = base_date + timedelta(days=day)
            
            # Update derived values
            state.update_derived_values()
            
            # Add to episodic states
            episodic_states.append(state)
        
        # Create temporal dynamics with episodic states
        episodic_dynamics = TemporalDynamics(
            pattern_detectors={
                "episodic": EpisodicPatternDetector(
                    detection_threshold=0.4,
                    episode_duration_range=(15, 30)
                )
            }
        )
        
        # Add all episodic states
        for state in episodic_states:
            episodic_dynamics.record_state_point(state)
        
        # Detect patterns
        patterns = episodic_dynamics.detect_patterns()
        
        # Verify episodes were detected
        assert "episodic" in patterns
        assert patterns["episodic"].strength > 0.5
        assert patterns["episodic"].confidence > 0.5
        assert patterns["episodic"].episode_count == 3
        assert 15 <= patterns["episodic"].avg_duration <= 25  # Should be close to 20 days
    
    def test_forecast_accuracy(self):
        """Test accuracy of forecasting model."""
        # Add first 7 test states to history
        for i in range(7):
            self.temporal_dynamics.record_state_point(self.test_states[i])
        
        # Initialize forecasting model
        self.temporal_dynamics.initialize_forecasters()
        
        # Forecast next 3 states
        forecast = self.temporal_dynamics.forecast_trajectory(days=30)
        
        # Compare forecast to actual values
        actual_mood_values = [self.test_states[i].psychological.mood_valence for i in range(7, 10)]
        actual_anxiety_values = [self.test_states[i].psychological.anxiety_level for i in range(7, 10)]
        
        # Calculate forecast points at the same timepoints as the test data
        forecast_indices = [0, 1, 2]  # The first three forecast points
        
        # Calculate RMSE for mood
        mood_errors = [
            (forecast.mood_values[i] - actual_mood_values[i])**2 
            for i in range(min(len(forecast_indices), len(actual_mood_values)))
        ]
        mood_rmse = np.sqrt(np.mean(mood_errors))
        
        # Calculate RMSE for anxiety
        anxiety_errors = [
            (forecast.anxiety_values[i] - actual_anxiety_values[i])**2 
            for i in range(min(len(forecast_indices), len(actual_anxiety_values)))
        ]
        anxiety_rmse = np.sqrt(np.mean(anxiety_errors))
        
        # Verify reasonable accuracy (RMSE should be < 0.3 for -1 to 1 scale)
        assert mood_rmse < 0.3
        assert anxiety_rmse < 0.3
        
        # Test validation metrics
        metrics = self.temporal_dynamics.validate_forecast_accuracy(
            self.test_states[7:10]
        )
        
        # Verify metrics
        assert "mood_valence" in metrics
        assert "anxiety_level" in metrics
        assert "sleep_quality" in metrics
        
        assert "rmse" in metrics["mood_valence"]
        assert "mae" in metrics["mood_valence"]
        assert metrics["mood_valence"]["rmse"] < 0.3
    
    def test_sliding_window(self):
        """Test sliding window functionality for state history."""
        # Create a long history
        long_dynamics = TemporalDynamics(history_window_days=30)
        
        # Add states spanning 60 days
        base_date = datetime.utcnow() - timedelta(days=60)
        for i in range(60):
            state = DigitalTwinState()
            state.timestamp = base_date + timedelta(days=i)
            long_dynamics.record_state_point(state)
        
        # Verify only the most recent 30 days are kept
        assert len(long_dynamics.state_history) <= 31  # Allow 1 extra for current day
        
        # Verify oldest record is within the window
        oldest_date = long_dynamics.state_history[0].timestamp
        newest_date = long_dynamics.state_history[-1].timestamp
        date_diff = (newest_date - oldest_date).days
        assert date_diff <= 30
    
    def test_treatment_effect_integration(self):
        """Test integration of treatment effects into forecasting."""
        # Add all test states to history
        for state in self.test_states:
            self.temporal_dynamics.record_state_point(state)
        
        # Initialize forecasting model
        self.temporal_dynamics.initialize_forecasters()
        
        # Forecast without treatment
        baseline_forecast = self.temporal_dynamics.forecast_trajectory(days=30)
        
        # Define treatment effects
        treatment_effects = {
            "serotonin_level": 0.3,
            "dopamine_level": 0.2,
            "mood_valence": 0.3,
            "anxiety_level": -0.3,
            "sleep_quality": 0.2,
            "activity_level": 0.3
        }
        
        # Forecast with treatment
        treatment_forecast = self.temporal_dynamics.forecast_with_intervention(
            treatment_effects,
            days=30
        )
        
        # Verify treatment improves outcomes
        assert treatment_forecast.mood_values[-1] > baseline_forecast.mood_values[-1]
        assert treatment_forecast.anxiety_values[-1] < baseline_forecast.anxiety_values[-1]
    
    def test_response_prediction_metrics(self):
        """Test metrics provided in treatment response prediction."""
        # Add all test states to history
        for state in self.test_states:
            self.temporal_dynamics.record_state_point(state)
        
        # Initialize forecasting model
        self.temporal_dynamics.initialize_forecasters()
        
        # Define treatment effects
        treatment_effects = {
            "serotonin_level": 0.3,
            "dopamine_level": 0.2,
            "mood_valence": 0.3,
            "anxiety_level": -0.3,
            "sleep_quality": 0.2
        }
        
        # Predict response
        response = self.temporal_dynamics.predict_treatment_response(
            treatment_effects,
            days=60
        )
        
        # Test response metrics
        assert 0.0 <= response["efficacy"] <= 1.0
        assert response["time_to_response"] > 0
        assert isinstance(response["time_to_response"], int)
        
        if "time_to_remission" in response:
            assert response["time_to_remission"] >= response["time_to_response"]
        
        assert 0.0 <= response["remission_probability"] <= 1.0
        
        # Verify conditional probability
        if response["remission_probability"] > 0:
            assert "expected_time_to_remission" in response
        
        # Verify confidence level
        assert "confidence" in response
        assert 0.0 <= response["confidence"] <= 1.0


class TestPatternDetectors(unittest.TestCase):
    """Tests for pattern detection algorithms."""
    
    def test_seasonal_detector(self):
        """Test seasonal pattern detector."""
        # Create detector
        detector = SeasonalPatternDetector(
            detection_threshold=0.5,
            minimum_cycles=1,
            periodicity_methods=["fft", "autocorrelation"]
        )
        
        # Create a simulated seasonal time series
        days = 365 * 2  # 2 years
        timestamps = [datetime.now() - timedelta(days=days-i) for i in range(days)]
        
        # Create sine wave with 365-day periodicity
        values = np.sin(np.arange(days) * 2 * np.pi / 365)
        
        # Add some noise
        values += np.random.normal(0, 0.1, days)
        
        # Create input data dictionary
        data = {
            "timestamps": timestamps,
            "values": values
        }
        
        # Detect patterns
        result = detector.detect(data)
        
        # Verify detection
        assert isinstance(result, PatternStrength)
        assert result.strength > 0.5
        assert result.confidence > 0.5
        assert 350 <= result.cycle_length <= 380  # Should be close to 365
    
    def test_episodic_detector(self):
        """Test episodic pattern detector."""
        # Create detector
        detector = EpisodicPatternDetector(
            detection_threshold=0.4,
            episode_duration_range=(10, 30)
        )
        
        # Create a simulated episodic time series
        days = 365  # 1 year
        timestamps = [datetime.now() - timedelta(days=days-i) for i in range(days)]
        
        # Create baseline values
        values = np.zeros(days)
        
        # Add 3 episodes
        episode_starts = [50, 150, 250]
        episode_length = 20
        
        for start in episode_starts:
            values[start:start+episode_length] = -0.8  # Depression episodes
        
        # Add some noise
        values += np.random.normal(0, 0.1, days)
        
        # Create input data dictionary
        data = {
            "timestamps": timestamps,
            "values": values
        }
        
        # Detect patterns
        result = detector.detect(data)
        
        # Verify detection
        assert isinstance(result, PatternStrength)
        assert result.strength > 0.5
        assert result.confidence > 0.5
        assert result.episode_count == 3
        assert 15 <= result.avg_duration <= 25  # Should be close to 20
    
    def test_custom_pattern_detector(self):
        """Test creation of custom pattern detector."""
        # Create a custom detector
        class CustomDetector(PatternDetector):
            def detect(self, data):
                # Simple detection algorithm
                values = data["values"]
                strength = np.abs(np.mean(values))
                confidence = min(1.0, 1.0 - np.std(values))
                
                return PatternStrength(
                    strength=strength,
                    confidence=confidence,
                    metadata={"mean": np.mean(values), "std": np.std(values)}
                )
        
        # Create instance
        detector = CustomDetector()
        
        # Create test data
        days = 100
        timestamps = [datetime.now() - timedelta(days=days-i) for i in range(days)]
        values = np.random.normal(0.5, 0.2, days)  # Mean 0.5, std 0.2
        
        data = {
            "timestamps": timestamps,
            "values": values
        }
        
        # Detect patterns
        result = detector.detect(data)
        
        # Verify detection
        assert isinstance(result, PatternStrength)
        assert 0.4 <= result.strength <= 0.6  # Should be close to 0.5
        assert "mean" in result.metadata
        assert "std" in result.metadata
        assert 0.4 <= result.metadata["mean"] <= 0.6


class TestTrajectoryPrediction(unittest.TestCase):
    """Tests for the TrajectoryPrediction entity."""
    
    def test_init(self):
        """Test initialization of trajectory prediction."""
        time_points = [0, 7, 14, 21, 28]
        mood_values = [-0.5, -0.4, -0.3, -0.2, -0.1]
        anxiety_values = [0.7, 0.6, 0.5, 0.4, 0.3]
        
        trajectory = TrajectoryPrediction(
            time_points=time_points,
            mood_values=mood_values,
            anxiety_values=anxiety_values
        )
        
        assert trajectory.time_points == time_points
        assert trajectory.mood_values == mood_values
        assert trajectory.anxiety_values == anxiety_values
        assert trajectory.confidence_intervals == {}
    
    def test_with_confidence_intervals(self):
        """Test trajectory with confidence intervals."""
        time_points = [0, 7, 14, 21, 28]
        mood_values = [-0.5, -0.4, -0.3, -0.2, -0.1]
        anxiety_values = [0.7, 0.6, 0.5, 0.4, 0.3]
        
        confidence_intervals = {
            "mood": [
                [-0.6, -0.4], [-0.5, -0.3], [-0.4, -0.2],
                [-0.3, -0.1], [-0.2, 0.0]
            ],
            "anxiety": [
                [0.6, 0.8], [0.5, 0.7], [0.4, 0.6],
                [0.3, 0.5], [0.2, 0.4]
            ]
        }
        
        trajectory = TrajectoryPrediction(
            time_points=time_points,
            mood_values=mood_values,
            anxiety_values=anxiety_values,
            confidence_intervals=confidence_intervals
        )
        
        assert trajectory.confidence_intervals == confidence_intervals
        assert len(trajectory.confidence_intervals["mood"]) == len(time_points)
        assert len(trajectory.confidence_intervals["anxiety"]) == len(time_points)
    
    def test_calculate_slope(self):
        """Test calculation of trajectory slope."""
        time_points = [0, 7, 14, 21, 28]
        mood_values = [-0.5, -0.4, -0.3, -0.2, -0.1]
        anxiety_values = [0.7, 0.6, 0.5, 0.4, 0.3]
        
        trajectory = TrajectoryPrediction(
            time_points=time_points,
            mood_values=mood_values,
            anxiety_values=anxiety_values
        )
        
        # Calculate slopes
        mood_slope = trajectory.calculate_slope("mood")
        anxiety_slope = trajectory.calculate_slope("anxiety")
        
        # Verify slopes
        assert mood_slope > 0  # Improving mood
        assert anxiety_slope < 0  # Decreasing anxiety
    
    def test_time_to_threshold(self):
        """Test calculation of time to reach threshold."""
        time_points = [0, 7, 14, 21, 28, 35, 42, 49, 56]
        mood_values = [-0.5, -0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3]
        anxiety_values = [0.7, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25]
        
        trajectory = TrajectoryPrediction(
            time_points=time_points,
            mood_values=mood_values,
            anxiety_values=anxiety_values
        )
        
        # Calculate time to reach thresholds
        mood_threshold_time = trajectory.time_to_threshold("mood", 0.0)
        anxiety_threshold_time = trajectory.time_to_threshold("anxiety", 0.4)
        
        # Verify threshold times
        assert mood_threshold_time == 35  # Day 35
        assert anxiety_threshold_time == 35  # Day 35
    
    def test_interpolate(self):
        """Test interpolation of trajectory values."""
        time_points = [0, 14, 28, 42, 56]
        mood_values = [-0.5, -0.3, -0.1, 0.1, 0.3]
        anxiety_values = [0.7, 0.6, 0.5, 0.4, 0.3]
        
        trajectory = TrajectoryPrediction(
            time_points=time_points,
            mood_values=mood_values,
            anxiety_values=anxiety_values
        )
        
        # Interpolate to get weekly values
        weekly_trajectory = trajectory.interpolate([0, 7, 14, 21, 28, 35, 42, 49, 56])
        
        # Verify interpolation
        assert len(weekly_trajectory.time_points) == 9
        assert len(weekly_trajectory.mood_values) == 9
        assert len(weekly_trajectory.anxiety_values) == 9
        
        # Check specific values
        assert weekly_trajectory.mood_values[0] == -0.5
        assert weekly_trajectory.mood_values[2] == -0.3
        assert weekly_trajectory.mood_values[4] == -0.1
        
        # Check interpolated values
        assert -0.5 < weekly_trajectory.mood_values[1] < -0.3
        assert -0.3 < weekly_trajectory.mood_values[3] < -0.1
    
    def test_calculate_response_metrics(self):
        """Test calculation of response metrics."""
        time_points = [0, 7, 14, 21, 28, 35, 42, 49, 56]
        mood_values = [-0.5, -0.4, -0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3]
        anxiety_values = [0.7, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3, 0.25]
        
        trajectory = TrajectoryPrediction(
            time_points=time_points,
            mood_values=mood_values,
            anxiety_values=anxiety_values
        )
        
        # Calculate response metrics with a 0.0 mood threshold
        response_metrics = trajectory.calculate_response_metrics(
            response_threshold={"mood": 0.0, "anxiety": 0.4},
            remission_threshold={"mood": 0.2, "anxiety": 0.3}
        )
        
        # Verify metrics
        assert "time_to_response" in response_metrics
        assert "time_to_remission" in response_metrics
        assert "probability_of_response" in response_metrics
        assert "probability_of_remission" in response_metrics
        
        assert response_metrics["time_to_response"] == 35  # Day 35
        assert response_metrics["time_to_remission"] == 49  # Day 49
        assert 0.0 <= response_metrics["probability_of_response"] <= 1.0
        assert 0.0 <= response_metrics["probability_of_remission"] <= 1.0


class TestTimeSeriesForecaster(unittest.TestCase):
    """Tests for the TimeSeriesForecaster component."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create a forecaster
        self.forecaster = TimeSeriesForecaster()
        
        # Create test data
        self.timestamps = [
            datetime.now() - timedelta(days=50-i) for i in range(50)
        ]
        
        # Linear trend with noise
        self.values = np.linspace(-0.5, 0.5, 50) + np.random.normal(0, 0.05, 50)
    
    def test_train_model(self):
        """Test training of forecasting model."""
        # Train model
        self.forecaster.train(self.timestamps, self.values)
        
        # Verify model is trained
        assert self.forecaster.is_trained
        assert self.forecaster.train_end_time == self.timestamps[-1]
    
    def test_forecast(self):
        """Test forecasting."""
        # Train model
        self.forecaster.train(self.timestamps, self.values)
        
        # Forecast next 10 days
        forecast = self.forecaster.forecast(days=10)
        
        # Verify forecast
        assert len(forecast["timestamps"]) == 10
        assert len(forecast["values"]) == 10
        assert len(forecast["lower_bound"]) == 10
        assert len(forecast["upper_bound"]) == 10
        
        # First timestamp should be after the last training timestamp
        assert forecast["timestamps"][0] > self.timestamps[-1]
        
        # Last forecast value should follow trend (positive in this case)
        assert forecast["values"][-1] > self.values[-1]
    
    def test_forecast_with_intervention(self):
        """Test forecasting with intervention effects."""
        # Train model
        self.forecaster.train(self.timestamps, self.values)
        
        # Define intervention effect
        intervention_effect = 0.2  # Positive effect
        
        # Forecast with intervention
        forecast_base = self.forecaster.forecast(days=10)
        forecast_with_intervention = self.forecaster.forecast_with_intervention(
            days=10,
            intervention_effect=intervention_effect
        )
        
        # Verify intervention effect
        for i in range(len(forecast_base["values"])):
            # The intervention forecast should be higher than the base forecast
            assert forecast_with_intervention["values"][i] > forecast_base["values"][i]
            
            # The difference should be close to the intervention effect
            # (exact match not expected due to model dynamics)
            diff = forecast_with_intervention["values"][i] - forecast_base["values"][i]
            assert intervention_effect * 0.5 <= diff <= intervention_effect * 1.5
    
    def test_validation(self):
        """Test validation of forecast accuracy."""
        # Use first 40 points for training
        train_timestamps = self.timestamps[:40]
        train_values = self.values[:40]
        
        # Use last 10 points for validation
        valid_timestamps = self.timestamps[40:]
        valid_values = self.values[40:]
        
        # Train model
        self.forecaster.train(train_timestamps, train_values)
        
        # Validate model
        metrics = self.forecaster.validate(valid_timestamps, valid_values)
        
        # Verify metrics
        assert "rmse" in metrics
        assert "mae" in metrics
        assert "r_squared" in metrics
        assert 0.0 <= metrics["rmse"]
        assert 0.0 <= metrics["mae"]
        assert metrics["r_squared"] <= 1.0
    
    def test_multiple_forecasters(self):
        """Test using multiple forecasters for different variables."""
        # Create forecasters for different variables
        mood_forecaster = TimeSeriesForecaster()
        anxiety_forecaster = TimeSeriesForecaster()
        
        # Create test data
        anxiety_values = np.linspace(0.7, 0.3, 50) + np.random.normal(0, 0.05, 50)
        
        # Train forecasters
        mood_forecaster.train(self.timestamps, self.values)
        anxiety_forecaster.train(self.timestamps, anxiety_values)
        
        # Forecast with each
        mood_forecast = mood_forecaster.forecast(days=10)
        anxiety_forecast = anxiety_forecaster.forecast(days=10)
        
        # Verify forecasts
        assert mood_forecast["values"][-1] > self.values[-1]  # Mood improving
        assert anxiety_forecast["values"][-1] < anxiety_values[-1]  # Anxiety decreasing


if __name__ == '__main__':
    unittest.main()