# -*- coding: utf-8 -*-
"""
Biometric Correlation Model Service for the NOVAMIND Digital Twin.

This module implements the service layer for the Biometric Correlation microservice,
providing analysis of relationships between biometric data and mental health indicators,
following Clean Architecture principles and HIPAA compliance requirements.
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from uuid import UUID

import numpy as np

from app.domain.exceptions import ModelInferenceError, ValidationError
from app.infrastructure.ml.biometric_correlation.lstm_model import (
    BiometricCorrelationModel,
)


class BiometricCorrelationService:
    """
    Service for analyzing correlations between biometric data and mental health.

    This service implements the core functionality of the Biometric Correlation
    microservice, providing a clean interface for the domain layer to interact
    with the ML models while maintaining separation of concerns and ensuring
    HIPAA compliance.
    """

    def __init__(
        self,
        model_dir: str,
        model_path: Optional[str] = None,
        biometric_features: Optional[List[str]] = None,
        mental_health_indicators: Optional[List[str]] = None,
    ):
        """
        Initialize the biometric correlation service.

        Args:
            model_dir: Directory for model storage
            model_path: Path to pretrained model
            biometric_features: Names of biometric features
            mental_health_indicators: Names of mental health indicators
        """
        self.model_dir = model_dir
        self.biometric_features = biometric_features or [
            "heart_rate",
            "sleep_duration",
            "sleep_quality",
            "steps",
            "activity_level",
            "hrv",
            "respiratory_rate",
            "body_temperature",
            "blood_pressure_systolic",
            "blood_pressure_diastolic",
        ]

        self.mental_health_indicators = mental_health_indicators or [
            "anxiety_level",
            "depression_level",
            "stress_level",
            "mood_score",
            "energy_level",
        ]

        # Create model directory if it doesn't exist
        os.makedirs(model_dir, exist_ok=True)

        # Initialize model
        self.model = BiometricCorrelationModel(
            model_path=model_path,
            input_dim=len(self.biometric_features),
            output_dim=len(self.mental_health_indicators),
        )

        logging.info("Biometric Correlation Service initialized")

    async def preprocess_biometric_data(
        self, patient_id: UUID, data: Dict[str, Any]
    ) -> Dict[str, np.ndarray]:
        """
        Preprocess biometric data for model input.

        Args:
            patient_id: UUID of the patient
            data: Raw patient data

        Returns:
            Dictionary containing preprocessed biometric and mental health data
        """
        try:
            # Extract time series data
            time_series = data.get("time_series", [])

            if not time_series:
                raise ValidationError("No time series data provided")

            # Extract biometric features
            biometric_data = []
            mental_health_data = []
            timestamps = []

            for entry in time_series:
                # Extract biometric features
                biometric_vector = []

                for feature in self.biometric_features:
                    biometric_vector.append(entry.get(feature, 0.0))

                biometric_data.append(biometric_vector)

                # Extract mental health indicators
                mental_health_vector = []

                for indicator in self.mental_health_indicators:
                    mental_health_vector.append(entry.get(indicator, 0.0))

                mental_health_data.append(mental_health_vector)

                # Extract timestamp
                timestamps.append(entry.get("timestamp", ""))

            # Convert to numpy arrays
            biometric_array = np.array(biometric_data, dtype=np.float32)
            mental_health_array = np.array(mental_health_data, dtype=np.float32)

            # Normalize biometric data (simple min-max scaling)
            for i in range(biometric_array.shape[1]):
                col_min = biometric_array[:, i].min()
                col_max = biometric_array[:, i].max()

                if col_max > col_min:
                    biometric_array[:, i] = (biometric_array[:, i] - col_min) / (
                        col_max - col_min
                    )

            # Normalize mental health data
            for i in range(mental_health_array.shape[1]):
                col_min = mental_health_array[:, i].min()
                col_max = mental_health_array[:, i].max()

                if col_max > col_min:
                    mental_health_array[:, i] = (
                        mental_health_array[:, i] - col_min
                    ) / (col_max - col_min)

            return {
                "biometric_data": biometric_array,
                "mental_health_data": mental_health_array,
                "timestamps": timestamps,
            }

        except Exception as e:
            logging.error(f"Error preprocessing biometric data: {str(e)}")
            raise ValidationError(f"Failed to preprocess biometric data: {str(e)}")

    async def analyze_correlations(
        self, patient_id: UUID, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze correlations between biometric data and mental health indicators.

        Args:
            patient_id: UUID of the patient
            data: Patient data

        Returns:
            Dictionary containing correlation analysis results
        """
        try:
            # Preprocess data
            preprocessed_data = await self.preprocess_biometric_data(patient_id, data)

            biometric_data = preprocessed_data["biometric_data"]
            mental_health_data = preprocessed_data["mental_health_data"]

            if biometric_data.shape[0] < 10:
                raise ValidationError(
                    "Insufficient time series data for correlation analysis (minimum 10 points required)"
                )

            # Identify key biometric indicators
            key_indicators = await self.model.identify_key_biometric_indicators(
                biometric_data, mental_health_data
            )

            # Calculate lag correlations (how biometric changes precede mental health changes)
            lag_correlations = await self._calculate_lag_correlations(
                biometric_data, mental_health_data
            )

            # Generate insights
            insights = await self._generate_insights(
                key_indicators,
                lag_correlations,
                self.biometric_features,
                self.mental_health_indicators,
            )

            # Combine results
            results = {
                "patient_id": str(patient_id),
                "key_indicators": key_indicators,
                "lag_correlations": lag_correlations,
                "insights": insights,
                "analysis_generated_at": datetime.utcnow().isoformat(),
                "data_points": biometric_data.shape[0],
                "biometric_features": self.biometric_features,
                "mental_health_indicators": self.mental_health_indicators,
            }

            return results

        except Exception as e:
            logging.error(f"Error analyzing correlations: {str(e)}")
            raise ModelInferenceError(f"Failed to analyze correlations: {str(e)}")

    async def _calculate_lag_correlations(
        self,
        biometric_data: np.ndarray,
        mental_health_data: np.ndarray,
        max_lag: int = 7,
    ) -> Dict[str, Any]:
        """
        Calculate lag correlations between biometric data and mental health indicators.

        Args:
            biometric_data: Numpy array of biometric data
            mental_health_data: Numpy array of mental health data
            max_lag: Maximum lag in days to consider

        Returns:
            Dictionary containing lag correlation results
        """
        num_samples = biometric_data.shape[0]

        if num_samples <= max_lag:
            max_lag = num_samples // 2

        # Initialize lag correlation results
        lag_results = {}

        for i, biometric_feature in enumerate(self.biometric_features):
            feature_results = {}

            for j, mental_indicator in enumerate(self.mental_health_indicators):
                lag_correlations = []

                # Calculate correlation for each lag
                for lag in range(max_lag + 1):
                    if lag == 0:
                        # Contemporaneous correlation
                        corr = np.corrcoef(
                            biometric_data[:, i], mental_health_data[:, j]
                        )[0, 1]
                    else:
                        # Lagged correlation (biometric -> mental health)
                        corr = np.corrcoef(
                            biometric_data[:-lag, i], mental_health_data[lag:, j]
                        )[0, 1]

                    lag_correlations.append(float(corr))

                # Find optimal lag (maximum absolute correlation)
                abs_correlations = np.abs(lag_correlations)
                optimal_lag = int(np.argmax(abs_correlations))
                optimal_correlation = lag_correlations[optimal_lag]

                feature_results[mental_indicator] = {
                    "lag_correlations": lag_correlations,
                    "optimal_lag": optimal_lag,
                    "optimal_correlation": optimal_correlation,
                }

            lag_results[biometric_feature] = feature_results

        return {"lag_results": lag_results, "max_lag": max_lag}

    async def _generate_insights(
        self,
        key_indicators: Dict[str, Any],
        lag_correlations: Dict[str, Any],
        biometric_features: List[str],
        mental_health_indicators: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Generate insights from correlation analysis.

        Args:
            key_indicators: Key biometric indicators
            lag_correlations: Lag correlation results
            biometric_features: Names of biometric features
            mental_health_indicators: Names of mental health indicators

        Returns:
            List of insights
        """
        insights = []

        # Extract top correlations
        top_indicators = key_indicators.get("key_indicators", [])

        for indicator in top_indicators[:5]:  # Top 5 indicators
            biometric_idx = indicator.get("biometric_index")
            mental_idx = indicator.get("mental_health_index")
            correlation = indicator.get("correlation")

            if biometric_idx is None or mental_idx is None or correlation is None:
                continue

            biometric_feature = biometric_features[biometric_idx]
            mental_indicator = mental_health_indicators[mental_idx]

            # Get lag information
            lag_info = (
                lag_correlations.get("lag_results", {})
                .get(biometric_feature, {})
                .get(mental_indicator, {})
            )
            optimal_lag = lag_info.get("optimal_lag", 0)
            optimal_correlation = lag_info.get("optimal_correlation", 0)

            # Generate insight
            insight_text = ""

            if abs(correlation) > 0.7:
                strength = "strong"
            elif abs(correlation) > 0.4:
                strength = "moderate"
            else:
                strength = "weak"

            if correlation > 0:
                direction = "positive"
            else:
                direction = "negative"

            insight_text = f"There is a {strength} {direction} correlation between {biometric_feature} and {mental_indicator}"

            if optimal_lag > 0 and abs(optimal_correlation) > 0.3:
                insight_text += f", with changes in {biometric_feature} preceding changes in {mental_indicator} by approximately {optimal_lag} days"

            insights.append(
                {
                    "biometric_feature": biometric_feature,
                    "mental_indicator": mental_indicator,
                    "correlation": correlation,
                    "optimal_lag": optimal_lag,
                    "optimal_correlation": optimal_correlation,
                    "insight_text": insight_text,
                    "importance": abs(correlation) * (1 + 0.5 * (optimal_lag > 0)),
                }
            )

        # Sort insights by importance
        insights.sort(key=lambda x: x.get("importance", 0), reverse=True)

        return insights

    async def detect_anomalies(
        self, patient_id: UUID, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Detect anomalies in biometric data that may indicate mental health changes.

        Args:
            patient_id: UUID of the patient
            data: Patient data

        Returns:
            Dictionary containing anomaly detection results
        """
        try:
            # Preprocess data
            preprocessed_data = await self.preprocess_biometric_data(patient_id, data)

            biometric_data = preprocessed_data["biometric_data"]
            mental_health_data = preprocessed_data["mental_health_data"]
            timestamps = preprocessed_data["timestamps"]

            if biometric_data.shape[0] < 14:
                raise ValidationError(
                    "Insufficient time series data for anomaly detection (minimum 14 points required)"
                )

            # Detect biometric anomalies
            biometric_anomalies = await self.model.detect_biometric_anomalies(
                biometric_data, window_size=7
            )

            # Analyze mental health changes following biometric anomalies
            mental_health_changes = await self._analyze_mental_health_changes(
                biometric_anomalies, mental_health_data, timestamps
            )

            # Generate insights
            insights = await self._generate_anomaly_insights(
                biometric_anomalies,
                mental_health_changes,
                self.biometric_features,
                self.mental_health_indicators,
            )

            # Combine results
            results = {
                "patient_id": str(patient_id),
                "biometric_anomalies": biometric_anomalies,
                "mental_health_changes": mental_health_changes,
                "insights": insights,
                "analysis_generated_at": datetime.utcnow().isoformat(),
                "data_points": biometric_data.shape[0],
                "biometric_features": self.biometric_features,
                "mental_health_indicators": self.mental_health_indicators,
            }

            return results

        except Exception as e:
            logging.error(f"Error detecting anomalies: {str(e)}")
            raise ModelInferenceError(f"Failed to detect anomalies: {str(e)}")

    async def _analyze_mental_health_changes(
        self,
        biometric_anomalies: Dict[str, Any],
        mental_health_data: np.ndarray,
        timestamps: List[str],
    ) -> Dict[str, Any]:
        """
        Analyze mental health changes following biometric anomalies.

        Args:
            biometric_anomalies: Biometric anomaly detection results
            mental_health_data: Numpy array of mental health data
            timestamps: List of timestamps

        Returns:
            Dictionary containing mental health change analysis
        """
        # Extract anomalies by time
        anomalies_by_time = biometric_anomalies.get("anomalies_by_time", {})

        # Initialize results
        mental_health_changes = {}

        for time_idx, anomalies in anomalies_by_time.items():
            time_idx = int(time_idx)

            # Check if we have enough data after the anomaly
            if time_idx + 7 >= mental_health_data.shape[0]:
                continue

            # Calculate mental health changes in the week following the anomaly
            pre_anomaly = mental_health_data[time_idx - 3 : time_idx, :]
            post_anomaly = mental_health_data[time_idx + 1 : time_idx + 8, :]

            pre_mean = np.mean(pre_anomaly, axis=0)
            post_mean = np.mean(post_anomaly, axis=0)

            # Calculate percent change
            percent_change = (post_mean - pre_mean) / (np.abs(pre_mean) + 1e-6) * 100

            # Record significant changes
            significant_changes = []

            for i, indicator in enumerate(self.mental_health_indicators):
                if abs(percent_change[i]) > 10:  # 10% change threshold
                    significant_changes.append(
                        {
                            "indicator": indicator,
                            "percent_change": float(percent_change[i]),
                            "pre_value": float(pre_mean[i]),
                            "post_value": float(post_mean[i]),
                            "direction": (
                                "increase" if percent_change[i] > 0 else "decrease"
                            ),
                        }
                    )

            # Add to results if there are significant changes
            if significant_changes:
                mental_health_changes[str(time_idx)] = {
                    "timestamp": (
                        timestamps[time_idx] if time_idx < len(timestamps) else ""
                    ),
                    "anomalies": anomalies,
                    "significant_changes": significant_changes,
                }

        return {
            "changes_by_time": mental_health_changes,
            "total_significant_periods": len(mental_health_changes),
        }

    async def _generate_anomaly_insights(
        self,
        biometric_anomalies: Dict[str, Any],
        mental_health_changes: Dict[str, Any],
        biometric_features: List[str],
        mental_health_indicators: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Generate insights from anomaly detection.

        Args:
            biometric_anomalies: Biometric anomaly detection results
            mental_health_changes: Mental health change analysis
            biometric_features: Names of biometric features
            mental_health_indicators: Names of mental health indicators

        Returns:
            List of insights
        """
        insights = []

        # Extract changes by time
        changes_by_time = mental_health_changes.get("changes_by_time", {})

        for time_idx, change_data in changes_by_time.items():
            anomalies = change_data.get("anomalies", [])
            significant_changes = change_data.get("significant_changes", [])

            # Group anomalies by feature
            anomalies_by_feature = {}

            for anomaly in anomalies:
                feature_idx = anomaly.get("feature_index")

                if feature_idx is not None and feature_idx < len(biometric_features):
                    feature = biometric_features[feature_idx]

                    if feature not in anomalies_by_feature:
                        anomalies_by_feature[feature] = []

                    anomalies_by_feature[feature].append(anomaly)

            # Generate insights for each feature with anomalies
            for feature, feature_anomalies in anomalies_by_feature.items():
                # Get the most severe anomaly
                most_severe = max(
                    feature_anomalies, key=lambda x: abs(x.get("z_score", 0))
                )
                severity = most_severe.get("severity", "medium")
                z_score = most_severe.get("z_score", 0)

                # Get associated mental health changes
                for change in significant_changes:
                    indicator = change.get("indicator")
                    direction = change.get("direction")
                    percent_change = change.get("percent_change")

                    if indicator and direction and percent_change is not None:
                        # Generate insight text
                        insight_text = f"A {severity} anomaly in {feature} (z-score: {z_score:.2f}) was followed by a {abs(percent_change):.1f}% {direction} in {indicator} within one week"

                        insights.append(
                            {
                                "biometric_feature": feature,
                                "mental_indicator": indicator,
                                "anomaly_severity": severity,
                                "z_score": z_score,
                                "percent_change": percent_change,
                                "direction": direction,
                                "insight_text": insight_text,
                                "importance": abs(z_score) * abs(percent_change) / 100,
                            }
                        )

        # Sort insights by importance
        insights.sort(key=lambda x: x.get("importance", 0), reverse=True)

        return insights

    async def recommend_monitoring_plan(
        self, patient_id: UUID, analysis_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recommend a personalized biometric monitoring plan based on analysis results.

        Args:
            patient_id: UUID of the patient
            analysis_results: Results from correlation analysis

        Returns:
            Dictionary containing monitoring recommendations
        """
        try:
            # Extract key indicators
            key_indicators = analysis_results.get("key_indicators", {}).get(
                "key_indicators", []
            )

            # Extract lag correlations
            lag_correlations = analysis_results.get("lag_correlations", {}).get(
                "lag_results", {}
            )

            # Identify most important biometric features to monitor
            important_features = []

            for indicator in key_indicators:
                biometric_idx = indicator.get("biometric_index")
                correlation = indicator.get("correlation")

                if (
                    biometric_idx is not None
                    and correlation is not None
                    and biometric_idx < len(self.biometric_features)
                ):
                    feature = self.biometric_features[biometric_idx]

                    # Check if feature is already in the list
                    if not any(
                        item["feature"] == feature for item in important_features
                    ):
                        # Get optimal lag information
                        lag_info = {}

                        for mental_indicator in self.mental_health_indicators:
                            if (
                                feature in lag_correlations
                                and mental_indicator in lag_correlations[feature]
                            ):
                                info = lag_correlations[feature][mental_indicator]

                                if (
                                    info.get("optimal_lag", 0) > 0
                                    and abs(info.get("optimal_correlation", 0)) > 0.3
                                ):
                                    lag_info[mental_indicator] = info

                        important_features.append(
                            {
                                "feature": feature,
                                "correlation": abs(correlation),
                                "lag_info": lag_info,
                            }
                        )

            # Sort by correlation strength
            important_features.sort(key=lambda x: x["correlation"], reverse=True)

            # Generate monitoring recommendations
            monitoring_recommendations = []

            for feature_data in important_features[:5]:  # Top 5 features
                feature = feature_data["feature"]
                lag_info = feature_data["lag_info"]

                # Determine monitoring frequency
                if feature in ["heart_rate", "steps", "activity_level"]:
                    frequency = "continuous"
                elif feature in ["sleep_duration", "sleep_quality"]:
                    frequency = "daily"
                else:
                    frequency = "weekly"

                # Determine alert thresholds based on lag information
                alert_thresholds = []

                for indicator, info in lag_info.items():
                    optimal_lag = info.get("optimal_lag", 0)
                    optimal_correlation = info.get("optimal_correlation", 0)

                    if optimal_lag > 0:
                        direction = (
                            "increase" if optimal_correlation > 0 else "decrease"
                        )

                        alert_thresholds.append(
                            {
                                "indicator": indicator,
                                "direction": direction,
                                "lag_days": optimal_lag,
                                "z_score_threshold": 2.0,
                            }
                        )

                monitoring_recommendations.append(
                    {
                        "feature": feature,
                        "monitoring_frequency": frequency,
                        "alert_thresholds": alert_thresholds,
                        "importance": feature_data["correlation"],
                    }
                )

            return {
                "patient_id": str(patient_id),
                "monitoring_recommendations": monitoring_recommendations,
                "recommended_features": [
                    item["feature"] for item in monitoring_recommendations
                ],
                "generated_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            logging.error(f"Error recommending monitoring plan: {str(e)}")
            raise ModelInferenceError(f"Failed to recommend monitoring plan: {str(e)}")

    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about the service.

        Returns:
            Dictionary containing service information
        """
        return {
            "service_name": "Biometric Correlation Service",
            "model": self.model.get_model_info(),
            "biometric_features": self.biometric_features,
            "mental_health_indicators": self.mental_health_indicators,
            "timestamp": datetime.utcnow().isoformat(),
        }
