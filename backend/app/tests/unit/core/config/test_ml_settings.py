"""Unit tests for ML configuration settings."""
import pytest
from unittest.mock import patch, MagicMock
import os
from typing import Dict, Any

from app.core.config.ml_settings import (
    MLSettings,
    MLModelType,
    MLFramework,
    get_ml_settings,
    load_model_config
)


@pytest.fixture
def sample_ml_config():
    """Create a sample ML configuration dictionary."""
    return {
        "model_path": "/models/symptom_prediction/",
        "model_type": "ensemble",
        "framework": "pytorch",
        "batch_size": 32,
        "use_gpu": True,
        "precision": "float16",
        "quantized": False,
        "inference_timeout": 5.0,
        "confidence_threshold": 0.75,
        "cache_results": True,
        "cache_ttl": 3600,
        "version": "1.2.3",
        "components": {
            "transformer": {
                "model_path": "/models/symptom_prediction/transformer/",
                "num_heads": 8,
                "embedding_dim": 512
            },
            "lstm": {
                "model_path": "/models/symptom_prediction/lstm/",
                "hidden_size": 256,
                "num_layers": 2
            }
        }
    }


@pytest.fixture
def ml_settings(sample_ml_config):
    """Create an MLSettings instance."""
    return MLSettings(
        model_path=sample_ml_config["model_path"],
        model_type=MLModelType(sample_ml_config["model_type"]),
        framework=MLFramework(sample_ml_config["framework"]),
        batch_size=sample_ml_config["batch_size"],
        use_gpu=sample_ml_config["use_gpu"],
        precision=sample_ml_config["precision"],
        quantized=sample_ml_config["quantized"],
        inference_timeout=sample_ml_config["inference_timeout"],
        confidence_threshold=sample_ml_config["confidence_threshold"],
        cache_results=sample_ml_config["cache_results"],
        cache_ttl=sample_ml_config["cache_ttl"],
        version=sample_ml_config["version"],
        components=sample_ml_config["components"]
    )


class TestMLSettings:
    """Test suite for MLSettings model."""
    
    def test_init(self, sample_ml_config):
        """Test initialization with valid settings."""
        settings = MLSettings(
            model_path=sample_ml_config["model_path"],
            model_type=MLModelType(sample_ml_config["model_type"]),
            framework=MLFramework(sample_ml_config["framework"]),
            batch_size=sample_ml_config["batch_size"],
            use_gpu=sample_ml_config["use_gpu"],
            precision=sample_ml_config["precision"],
            quantized=sample_ml_config["quantized"],
            inference_timeout=sample_ml_config["inference_timeout"],
            confidence_threshold=sample_ml_config["confidence_threshold"],
            cache_results=sample_ml_config["cache_results"],
            cache_ttl=sample_ml_config["cache_ttl"],
            version=sample_ml_config["version"],
            components=sample_ml_config["components"]
        )
        
        # Verify properties match input values
        assert settings.model_path == sample_ml_config["model_path"]
        assert settings.model_type == MLModelType(sample_ml_config["model_type"])
        assert settings.framework == MLFramework(sample_ml_config["framework"])
        assert settings.batch_size == sample_ml_config["batch_size"]
        assert settings.use_gpu == sample_ml_config["use_gpu"]
        assert settings.precision == sample_ml_config["precision"]
        assert settings.quantized == sample_ml_config["quantized"]
        assert settings.inference_timeout == sample_ml_config["inference_timeout"]
        assert settings.confidence_threshold == sample_ml_config["confidence_threshold"]
        assert settings.cache_results == sample_ml_config["cache_results"]
        assert settings.cache_ttl == sample_ml_config["cache_ttl"]
        assert settings.version == sample_ml_config["version"]
        assert settings.components == sample_ml_config["components"]
    
    def test_default_values(self):
        """Test that default values are set correctly."""
        # Create with minimal required fields
        settings = MLSettings(
            model_path="/models/minimal/",
            model_type=MLModelType.TRANSFORMER,
            framework=MLFramework.PYTORCH
        )
        
        # Check default values
        assert settings.batch_size == 1  # Default batch size
        assert settings.use_gpu is False  # Default GPU setting
        assert settings.precision == "float32"  # Default precision
        assert settings.quantized is False  # Default quantization
        assert settings.inference_timeout == 10.0  # Default timeout
        assert settings.confidence_threshold == 0.5  # Default confidence
        assert settings.cache_results is False  # Default caching
        assert settings.cache_ttl == 300  # Default TTL
        assert settings.version == "1.0.0"  # Default version
        assert settings.components == {}  # Default components
    
    def test_model_type_enum(self):
        """Test the MLModelType enum."""
        # Check enum values
        assert MLModelType.TRANSFORMER.value == "transformer"
        assert MLModelType.ENSEMBLE.value == "ensemble"
        assert MLModelType.LSTM.value == "lstm"
        assert MLModelType.CNN.value == "cnn"
        assert MLModelType.MLP.value == "mlp"
        
        # Check creating enum from string
        assert MLModelType("transformer") == MLModelType.TRANSFORMER
        assert MLModelType("ensemble") == MLModelType.ENSEMBLE
    
    def test_framework_enum(self):
        """Test the MLFramework enum."""
        # Check enum values
        assert MLFramework.PYTORCH.value == "pytorch"
        assert MLFramework.TENSORFLOW.value == "tensorflow"
        assert MLFramework.ONNX.value == "onnx"
        assert MLFramework.SCIKIT.value == "scikit-learn"
        
        # Check creating enum from string
        assert MLFramework("pytorch") == MLFramework.PYTORCH
        assert MLFramework("tensorflow") == MLFramework.TENSORFLOW
    
    def test_to_dict(self, ml_settings, sample_ml_config):
        """Test conversion to dictionary."""
        # Convert to dict
        settings_dict = ml_settings.to_dict()
        
        # Verify dict matches original config (with enum string values)
        assert settings_dict["model_path"] == sample_ml_config["model_path"]
        assert settings_dict["model_type"] == sample_ml_config["model_type"]
        assert settings_dict["framework"] == sample_ml_config["framework"]
        assert settings_dict["batch_size"] == sample_ml_config["batch_size"]
        assert settings_dict["use_gpu"] == sample_ml_config["use_gpu"]
        assert settings_dict["components"] == sample_ml_config["components"]
    
    def test_from_dict(self, sample_ml_config):
        """Test creation from dictionary."""
        # Create from dict
        settings = MLSettings.from_dict(sample_ml_config)
        
        # Verify properties match input config
        assert settings.model_path == sample_ml_config["model_path"]
        assert settings.model_type == MLModelType(sample_ml_config["model_type"])
        assert settings.framework == MLFramework(sample_ml_config["framework"])
        assert settings.batch_size == sample_ml_config["batch_size"]
        assert settings.components == sample_ml_config["components"]
    
    def test_validation(self):
        """Test validation of MLSettings."""
        # Test invalid batch size
        with pytest.raises(ValueError):
            MLSettings(
                model_path="/models/test/",
                model_type=MLModelType.TRANSFORMER,
                framework=MLFramework.PYTORCH,
                batch_size=0  # Invalid - should be positive
            )
        
        # Test invalid confidence threshold
        with pytest.raises(ValueError):
            MLSettings(
                model_path="/models/test/",
                model_type=MLModelType.TRANSFORMER,
                framework=MLFramework.PYTORCH,
                confidence_threshold=1.5  # Invalid - should be between 0 and 1
            )
        
        # Test invalid cache TTL
        with pytest.raises(ValueError):
            MLSettings(
                model_path="/models/test/",
                model_type=MLModelType.TRANSFORMER,
                framework=MLFramework.PYTORCH,
                cache_results=True,
                cache_ttl=-10  # Invalid - should be positive
            )


class TestMLSettingsConfig:
    """Test suite for ML settings configuration functions."""
    
    @patch("app.core.config.ml_settings.get_settings")
    def test_get_ml_settings(self, mock_get_settings):
        """Test getting ML settings from general settings."""
        # Mock settings to return ML path
        mock_settings = MagicMock()
        mock_settings.ML_CONFIG_PATH = "/config/ml/"
        mock_get_settings.return_value = mock_settings
        
        # Mock load function to return test settings
        with patch("app.core.config.ml_settings.load_model_config") as mock_load:
            mock_load.return_value = {
                "model_path": "/models/test/",
                "model_type": "transformer",
                "framework": "pytorch"
            }
            
            # Get settings for a model type
            settings = get_ml_settings("symptom_prediction")
            
            # Verify correct settings were loaded
            mock_load.assert_called_once_with(os.path.join("/config/ml/", "symptom_prediction.json"))
            assert settings.model_path == "/models/test/"
            assert settings.model_type == MLModelType.TRANSFORMER
    
    @patch("app.core.config.ml_settings.open")
    @patch("app.core.config.ml_settings.json.load")
    def test_load_model_config(self, mock_json_load, mock_open):
        """Test loading model configuration from file."""
        # Mock JSON loading
        test_config = {
            "model_path": "/models/test/",
            "model_type": "transformer",
            "framework": "pytorch"
        }
        mock_json_load.return_value = test_config
        
        # Load config
        config = load_model_config("/config/ml/symptom_prediction.json")
        
        # Verify file was opened and config loaded
        mock_open.assert_called_once_with("/config/ml/symptom_prediction.json", "r")
        assert config == test_config
    
    @patch("app.core.config.ml_settings.open")
    def test_load_model_config_file_not_found(self, mock_open):
        """Test handling of missing configuration file."""
        # Mock file not found
        mock_open.side_effect = FileNotFoundError("File not found")
        
        # Should raise FileNotFoundError
        with pytest.raises(FileNotFoundError):
            load_model_config("/config/ml/nonexistent.json")
    
    @patch("app.core.config.ml_settings.open")
    @patch("app.core.config.ml_settings.json.load")
    def test_load_model_config_invalid_json(self, mock_json_load, mock_open):
        """Test handling of invalid JSON configuration file."""
        # Mock JSON parsing error
        mock_json_load.side_effect = ValueError("Invalid JSON")
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            load_model_config("/config/ml/invalid.json")