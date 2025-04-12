import pytest
"""
Tests for the configuration module.

This module tests that application configuration loads correctly
and handles environment variables properly.
"""
import os

from app.core.config import Settings


@pytest.mark.db_required()
class TestSettings:
    """Test cases for the Settings class."""
    
    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        settings = Settings()
        
        # Check essential configuration values
    assert settings.PROJECT_NAME  ==  "Novamind Digital Twin"
    assert settings.API_PREFIX  ==  "/api/v1"
    assert settings.ENVIRONMENT  ==  "development"
        
        # Security settings
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES  ==  30
        
        # HIPAA settings
    assert settings.ENABLE_PHI_AUDITING is True
    
    def test_environment_override(self, monkeypatch):
        """Test that environment variables can override settings."""
        # Setup environment variables
        monkeypatch.setenv("PROJECT_NAME", "Custom Project Name")
        monkeypatch.setenv("API_VERSION", "v2")
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")  # 1 hour
        monkeypatch.setenv("ENABLE_PHI_AUDITING", "False")
        
        # Load settings with environment variables
    settings = Settings()
        
        # Check that environment variables were applied
    assert settings.PROJECT_NAME  ==  "Custom Project Name"
    assert settings.API_PREFIX  ==  "/api/v2"
    assert settings.ENVIRONMENT  ==  "production"
    assert settings.ACCESS_TOKEN_EXPIRE_MINUTES  ==  60
    assert settings.ENABLE_PHI_AUDITING is False
    
    def test_database_url_construction(self, monkeypatch):
        """Test that database URL is constructed correctly from components."""
        # Setup database environment variables
        test_db_url = "postgresql://test-user:test-password@test-db-server:5432/test-db"
        monkeypatch.setenv("DATABASE_URL", test_db_url)
        
        # Load settings
    settings = Settings()
        
        # Check database URL
    assert str(settings.SQLALCHEMY_DATABASE_URI) == test_db_url
    
    def test_testing_environment(self, monkeypatch):
        """Test that testing environment settings are applied."""
        # Setup testing environment
        monkeypatch.setenv("TESTING", "1")
        monkeypatch.setenv("ENVIRONMENT", "testing")
        
        # Load settings
    settings = Settings()
        
        # Verify testing environment settings
    assert settings.ENVIRONMENT  ==  "testing"
    assert "DEBUG" in os.environ
    
    def test_cors_settings(self, monkeypatch):
        """Test CORS origins settings parsing."""
        # Test comma-separated string format
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost,https://example.com")
        
    settings = Settings()
    assert len(settings.CORS_ORIGINS) == 2
    assert "http://localhost" in settings.CORS_ORIGINS
    assert "https://example.com" in settings.CORS_ORIGINS
        
        # Test list format
    monkeypatch.setenv("CORS_ORIGINS", '["http://localhost:8000", "https://api.example.com"]')
        
    settings = Settings()
    assert len(settings.CORS_ORIGINS) == 2
    assert "http://localhost:8000" in settings.CORS_ORIGINS
    assert "https://api.example.com" in settings.CORS_ORIGINS