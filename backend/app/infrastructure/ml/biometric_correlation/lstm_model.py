# -*- coding: utf-8 -*-
"""
LSTM-based biometric correlation model for the NOVAMIND Digital Twin.

This module implements a deep learning model for correlating biometric data
with mental health indicators, following the architecture described in
the AI Models Core Implementation documentation.
"""

import logging
from datetime import datetime, UTC, UTC
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from app.domain.exceptions import ModelInferenceError, ValidationError


class BiometricLSTM(nn.Module):
    """
    LSTM model for biometric-mental health correlation.

    This model processes multivariate time series data from biometric sources
    (heart rate, sleep patterns, activity levels) to identify correlations
    with mental health indicators.
    """

    def __init__(
        self,
        input_dim: int,
        hidden_dim: int,
        output_dim: int,
        num_layers: int = 2,
        dropout: float = 0.2,
        bidirectional: bool = True,
    ):
        """
        Initialize the LSTM model.

        Args:
            input_dim: Dimension of input features
            hidden_dim: Dimension of hidden state
            output_dim: Dimension of output
            num_layers: Number of LSTM layers
            dropout: Dropout rate
            bidirectional: Whether to use bidirectional LSTM
        """
        super().__init__()

        self.input_dim = input_dim
        self.hidden_dim = hidden_dim
        self.output_dim = output_dim
        self.num_layers = num_layers
        self.bidirectional = bidirectional

        # LSTM layers
        self.lstm = nn.LSTM(
            input_size=input_dim,
            hidden_size=hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
            bidirectional=bidirectional,
        )

        # Output layer
        self.fc = nn.Linear(hidden_dim * 2 if bidirectional else hidden_dim, output_dim)

        # Attention mechanism
        self.attention = nn.Linear(hidden_dim * 2 if bidirectional else hidden_dim, 1)

    def attention_net(
        self, lstm_output: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Apply attention mechanism to LSTM output.

        Args:
            lstm_output: Output from LSTM layer

        Returns:
            Tuple of context vector and attention weights
        """
        # Calculate attention scores
        attn_weights = self.attention(lstm_output)
        attn_weights = torch.tanh(attn_weights)
        attn_weights = F.softmax(attn_weights, dim=1)

        # Apply attention weights to LSTM output
        context = torch.bmm(lstm_output.transpose(1, 2), attn_weights)
        context = context.squeeze(2)

        return context, attn_weights

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass for the LSTM model.

        Args:
            x: Input tensor of shape (batch_size, seq_len, input_dim)

        Returns:
            Tuple of output and attention weights
        """
        # LSTM forward pass
        lstm_output, _ = self.lstm(x)

        # Apply attention
        context, attn_weights = self.attention_net(lstm_output)

        # Final output layer
        output = self.fc(context)

        return output, attn_weights


class BiometricCorrelationModel:
    """
    High-level wrapper for the Biometric Correlation LSTM model.

    This class provides an interface for the domain layer to interact with
    the LSTM model for biometric-mental health correlation analysis.
    """

    def __init__(
        self,
        model_path: Optional[str] = None,
        input_dim: int = 10,
        hidden_dim: int = 128,
        output_dim: int = 5,
        num_layers: int = 2,
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
    ):
        """
        Initialize the biometric correlation model.

        Args:
            model_path: Optional path to a pretrained model
            input_dim: Dimension of input features
            hidden_dim: Dimension of hidden state
            output_dim: Dimension of output
            num_layers: Number of LSTM layers
            device: Device to run the model on
        """
        self.device = device
        self.model = BiometricLSTM(
            input_dim=input_dim,
            hidden_dim=hidden_dim,
            output_dim=output_dim,
            num_layers=num_layers,
            dropout=0.2,
            bidirectional=True,
        ).to(device)

        # Load pretrained model if provided
        if model_path:
            try:
                # Load model with pickle_module=None for security
                state_dict = torch.load(
                    model_path,
                    map_location=device,
                    pickle_module=None,  # Disable pickle for security
                    weights_only=True,  # Only load model weights
                )
                # Validate state dict structure before loading
                expected_keys = {name for name, _ in self.model.named_parameters()}
                if not all(key in expected_keys for key in state_dict.keys()):
                    raise ValueError("Invalid model structure detected")

                self.model.load_state_dict(state_dict)
                logging.info(f"Loaded biometric correlation model from {model_path}")
            except Exception as e:
                logging.error(f"Error loading biometric correlation model: {str(e)}")
                raise ModelInferenceError(
                    f"Failed to load biometric correlation model: {str(e)}"
                )

        self.model.eval()

    async def analyze_biometric_data(
        self, biometric_data: np.ndarray
    ) -> Dict[str, Any]:
        """
        Analyze biometric data to identify correlations with mental health indicators.

        Args:
            biometric_data: Numpy array of biometric time series data

        Returns:
            Dictionary containing analysis results
        """
        try:
            # Convert numpy array to tensor
            input_tensor = torch.tensor(biometric_data, dtype=torch.float32).to(
                self.device
            )

            # Add batch dimension if needed
            if input_tensor.dim() == 2:
                input_tensor = input_tensor.unsqueeze(0)

            # Forward pass
            with torch.no_grad():
                output, attention_weights = self.model(input_tensor)

            # Convert to numpy arrays
            output_np = output.cpu().numpy()
            attention_weights_np = attention_weights.cpu().numpy()

            return {
                "predictions": output_np,
                "attention_weights": attention_weights_np,
                "model_type": "lstm",
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logging.error(f"Error analyzing biometric data: {str(e)}")
            raise ModelInferenceError(f"Failed to analyze biometric data: {str(e)}")

    async def identify_key_biometric_indicators(
        self, biometric_data: np.ndarray, mental_health_indicators: np.ndarray
    ) -> Dict[str, Any]:
        """
        Identify key biometric indicators correlated with mental health.

        Args:
            biometric_data: Numpy array of biometric time series data
            mental_health_indicators: Numpy array of mental health indicators

        Returns:
            Dictionary containing key indicators and their correlations
        """
        try:
            # Calculate correlation matrix
            combined_data = np.concatenate(
                [biometric_data, mental_health_indicators], axis=1
            )
            correlation_matrix = np.corrcoef(combined_data.T)

            # Extract correlations between biometric data and mental health indicators
            num_biometric = biometric_data.shape[1]
            num_mental = mental_health_indicators.shape[1]

            correlations = correlation_matrix[
                :num_biometric, num_biometric : num_biometric + num_mental
            ]

            # Identify key indicators (highest absolute correlations)
            key_indicators = []

            for i in range(num_biometric):
                for j in range(num_mental):
                    correlation = correlations[i, j]

                    key_indicators.append(
                        {
                            "biometric_index": i,
                            "mental_health_index": j,
                            "correlation": float(correlation),
                            "strength": abs(float(correlation)),
                        }
                    )

            # Sort by correlation strength
            key_indicators.sort(key=lambda x: x["strength"], reverse=True)

            # Analyze with LSTM model
            lstm_analysis = await self.analyze_biometric_data(biometric_data)

            return {
                "key_indicators": key_indicators[:10],  # Top 10 indicators
                "correlation_matrix": correlations.tolist(),
                "lstm_analysis": lstm_analysis,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logging.error(f"Error identifying key biometric indicators: {str(e)}")
            raise ModelInferenceError(
                f"Failed to identify key biometric indicators: {str(e)}"
            )

    async def detect_biometric_anomalies(
        self, biometric_data: np.ndarray, window_size: int = 7
    ) -> Dict[str, Any]:
        """
        Detect anomalies in biometric data that may indicate mental health changes.

        Args:
            biometric_data: Numpy array of biometric time series data
            window_size: Size of the sliding window for anomaly detection

        Returns:
            Dictionary containing detected anomalies
        """
        try:
            # Calculate moving average and standard deviation
            num_samples, num_features = biometric_data.shape

            if num_samples < window_size * 2:
                raise ValidationError(
                    f"Insufficient data points for anomaly detection (minimum {window_size * 2} required)"
                )

            # Initialize arrays for moving statistics
            moving_avg = np.zeros_like(biometric_data)
            moving_std = np.zeros_like(biometric_data)

            # Calculate moving statistics
            for i in range(num_samples):
                start_idx = max(0, i - window_size)
                end_idx = i + 1

                window_data = biometric_data[start_idx:end_idx, :]

                moving_avg[i, :] = np.mean(window_data, axis=0)
                moving_std[i, :] = np.std(window_data, axis=0)

            # Detect anomalies (Z-score > 2.0)
            z_scores = np.zeros_like(biometric_data)

            for i in range(window_size, num_samples):
                z_scores[i, :] = (biometric_data[i, :] - moving_avg[i - 1, :]) / (
                    moving_std[i - 1, :] + 1e-6
                )

            # Identify anomalies
            anomalies = []

            for i in range(window_size, num_samples):
                for j in range(num_features):
                    if abs(z_scores[i, j]) > 2.0:
                        anomalies.append(
                            {
                                "time_index": i,
                                "feature_index": j,
                                "value": float(biometric_data[i, j]),
                                "z_score": float(z_scores[i, j]),
                                "severity": (
                                    "high" if abs(z_scores[i, j]) > 3.0 else "medium"
                                ),
                            }
                        )

            # Group anomalies by time
            anomalies_by_time = {}

            for anomaly in anomalies:
                time_idx = anomaly["time_index"]

                if time_idx not in anomalies_by_time:
                    anomalies_by_time[time_idx] = []

                anomalies_by_time[time_idx].append(anomaly)

            # Analyze with LSTM model
            lstm_analysis = await self.analyze_biometric_data(biometric_data)

            return {
                "anomalies": anomalies,
                "anomalies_by_time": anomalies_by_time,
                "z_scores": z_scores.tolist(),
                "lstm_analysis": lstm_analysis,
                "window_size": window_size,
                "timestamp": datetime.now(UTC).isoformat(),
            }

        except Exception as e:
            logging.error(f"Error detecting biometric anomalies: {str(e)}")
            raise ModelInferenceError(f"Failed to detect biometric anomalies: {str(e)}")

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the model.

        Returns:
            Dictionary containing model information
        """
        return {
            "model_type": "Bidirectional LSTM with Attention",
            "input_dim": self.model.input_dim,
            "hidden_dim": self.model.hidden_dim,
            "output_dim": self.model.output_dim,
            "num_layers": self.model.num_layers,
            "bidirectional": self.model.bidirectional,
            "device": self.device,
            "parameter_count": sum(p.numel() for p in self.model.parameters()),
            "timestamp": datetime.now(UTC).isoformat(),
        }
