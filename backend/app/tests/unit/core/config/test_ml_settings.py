# -*- coding: utf-8 -*-
"""
Tests for ML Settings Configuration.

This module contains unit tests for ML (Machine Learning) settings configuration,
ensuring proper loading and validation of settings.
"""

import os
import pytest
from unittest.mock import patch

from app.core.config.ml_settings import MLSettings
@pytest.fixture
def default_ml_settings():
        """Fixture providing default ML settings."""    return MLSettings()


@pytest.mark.venv_only
def test_default_values(default_ml_settings):
    """Test that default values are set correctly."""
    # Check default directories
    assert default_ml_settings.MODEL_BASE_DIR == "./resources/models"
    assert default_ml_settings.XGBOOST_MODEL_DIR == "./resources/models/xgboost"
    assert default_ml_settings.MENTALLAMA_MODEL_DIR == "./resources/models/mentallama"
    
    # Check feature flags
    assert default_ml_settings.FEATURE_DIGITAL_TWIN is True
    assert default_ml_settings.FEATURE_ML_RISK_ASSESSMENT is True
    assert default_ml_settings.FEATURE_PHI_DETECTION is True
    
    # Check processing settings
    assert default_ml_settings.BATCH_SIZE == 64
    assert default_ml_settings.MAX_TEXT_LENGTH == 4096


@patch.dict(os.environ, {
    "MODEL_BASE_DIR": "/custom/models",
    "XGBOOST_MODEL_DIR": "/custom/models/xgboost",
    "MENTALLAMA_MODEL_DIR": "/custom/models/mentallama",
    "FEATURE_DIGITAL_TWIN": "false",
    "FEATURE_ML_RISK_ASSESSMENT": "false",
    "FEATURE_PHI_DETECTION": "false",
    "BATCH_SIZE": "128",
    "MAX_TEXT_LENGTH": "8192"
})
def test_environment_variable_override():
    """Test that environment variables override default values."""
    settings = MLSettings()
    
    # Check overridden directories
    assert settings.MODEL_BASE_DIR == "/custom/models"
    assert settings.XGBOOST_MODEL_DIR == "/custom/models/xgboost"
    assert settings.MENTALLAMA_MODEL_DIR == "/custom/models/mentallama"
    
    # Check overridden feature flags
    assert settings.FEATURE_DIGITAL_TWIN is False
    assert settings.FEATURE_ML_RISK_ASSESSMENT is False
    assert settings.FEATURE_PHI_DETECTION is False
    
    # Check overridden processing settings
    assert settings.BATCH_SIZE == 128
    assert settings.MAX_TEXT_LENGTH == 8192
def test_directory_creation(tmp_path):
    """Test that model directories are created if they don't exist."""
    # Create temporary directories for testing
    base_dir = tmp_path / "models"
    xgboost_dir = base_dir / "xgboost"
    mentallama_dir = base_dir / "mentallama"
    
    # Set environment variables to use these directories
    with patch.dict(os.environ, {})
"MODEL_BASE_DIR": str(base_dir),
        "XGBOOST_MODEL_DIR": str(xgboost_dir),
        "MENTALLAMA_MODEL_DIR": str(mentallama_dir)
})
        # Initialize settings
        settings = MLSettings()
        
        # Manually trigger directory creation (normally done on service startup)
settings.create_directories()
        
        # Check that directories were created
        assert base_dir.exists()
assert xgboost_dir.exists()
assert mentallama_dir.exists()
def test_model_path_creation():
    """Test creating model paths with version and variant."""
    settings = MLSettings()
    
    # Test with default base path
    path = settings.get_model_path("xgboost", "classifier", "v1", "standard")
expected = "./resources/models/xgboost/classifier/v1/standard"
    assert path == expected
    
    # Test with custom base path
    with patch.dict(os.environ, {"XGBOOST_MODEL_DIR": "/custom/models/xgboost"}):
        settings = MLSettings()
path = settings.get_model_path("xgboost", "classifier", "v1", "standard")
expected = "/custom/models/xgboost/classifier/v1/standard"
        assert path == expected
def test_digital_twin_settings(default_ml_settings):
    """Test Digital Twin specific settings."""
    # Check default Digital Twin settings
    assert default_ml_settings.DIGITAL_TWIN_RESOLUTION == "high"
    assert default_ml_settings.DIGITAL_TWIN_REGIONS == 84  # Default brain atlas regions
    
    # Test with custom settings
    with patch.dict(os.environ, {})
"DIGITAL_TWIN_RESOLUTION": "medium",
        "DIGITAL_TWIN_REGIONS": "42"
    }):
        settings = MLSettings()
assert settings.DIGITAL_TWIN_RESOLUTION == "medium"
        assert settings.DIGITAL_TWIN_REGIONS == 42
def test_xgboost_settings(default_ml_settings):
    """Test XGBoost specific settings."""
    # Check default XGBoost settings
    assert default_ml_settings.XGBOOST_THREADS == 4
    assert default_ml_settings.XGBOOST_GPU_ENABLED is False
    
    # Test with custom settings
    with patch.dict(os.environ, {})
"XGBOOST_THREADS": "8",
        "XGBOOST_GPU_ENABLED": "true"
    }):
        settings = MLSettings()
assert settings.XGBOOST_THREADS == 8
        assert settings.XGBOOST_GPU_ENABLED is True
def test_phi_detection_settings(default_ml_settings):
    """Test PHI detection specific settings."""
    # Check default PHI detection settings
    assert default_ml_settings.PHI_PATTERN_FILE == "phi_patterns.yaml"
    assert default_ml_settings.PHI_REDACTION_ENABLED is True
    
    # Test with custom settings
    with patch.dict(os.environ, {})
"PHI_PATTERN_FILE": "custom_patterns.yaml",
        "PHI_REDACTION_ENABLED": "false"
    }):
        settings = MLSettings()
assert settings.PHI_PATTERN_FILE == "custom_patterns.yaml"
        assert settings.PHI_REDACTION_ENABLED is False
def test_validation():
    """Test validation of settings."""
    # Test with invalid value for batch size
    with patch.dict(os.environ, {"BATCH_SIZE": "-1"}):
        with pytest.raises(ValueError, match="must be a positive integer"):
            MLSettings()
            
    # Test with invalid value for max text length
    with patch.dict(os.environ, {"MAX_TEXT_LENGTH": "0"}):
                with pytest.raises(ValueError, match="must be a positive integer"):
                    MLSettings()
            
    # Test with invalid value for Digital Twin resolution
    with patch.dict(os.environ, {"DIGITAL_TWIN_RESOLUTION": "invalid"}):
                        with pytest.raises(ValueError, match="must be one of"):
                            MLSettings()