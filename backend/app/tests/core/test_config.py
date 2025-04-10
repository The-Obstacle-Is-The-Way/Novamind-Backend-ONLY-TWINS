"""
Tests for the configuration module.

This module tests that application configuration loads correctly
and handles environment variables properly.
"""
import os
import pytest
from pathlib import Path

from app.core.config import Settings


class TestSettings:
    """Test cases for the Settings class."""
    
    def test_default_settings(self):
        """Test that default settings are loaded correctly."""
        settings = Settings()
        
        # Check essential configuration values
        assert settings.PROJECT_NAME == "Novamind Digital Twin"
        assert settings.API_V1_STR == "/api/v1"
        assert settings.ENVIRONMENT == "development"
        
        # Security settings
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60 * 24 * 7  # 7 days
        
        # HIPAA settings
        assert settings.AUDIT_LOG_ENABLED is True
        assert settings.PHI_ANONYMIZATION_ENABLED is True
        assert settings.SESSION_TIMEOUT_MINUTES == 30
    
    def test_environment_override(self, monkeypatch):
        """Test that environment variables can override settings."""
        # Setup environment variables
        monkeypatch.setenv("PROJECT_NAME", "Custom Project Name")
        monkeypatch.setenv("API_V1_STR", "/api/v2")
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")  # 1 hour
        monkeypatch.setenv("AUDIT_LOG_ENABLED", "False")
        
        # Load settings with environment variables
        settings = Settings()
        
        # Check that environment variables were applied
        assert settings.PROJECT_NAME == "Custom Project Name"
        assert settings.API_V1_STR == "/api/v2"
        assert settings.ENVIRONMENT == "production"
        assert settings.ACCESS_TOKEN_EXPIRE_MINUTES == 60
        assert settings.AUDIT_LOG_ENABLED is False
    
    def test_database_url_construction(self, monkeypatch):
        """Test that database URL is constructed correctly from components."""
        # Setup database environment variables
        monkeypatch.setenv("POSTGRES_SERVER", "test-db-server")
        monkeypatch.setenv("POSTGRES_USER", "test-user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test-password")
        monkeypatch.setenv("POSTGRES_DB", "test-db")
        
        # Load settings
        settings = Settings()
        
        # Check database URL
        expected_url = "postgresql+asyncpg://test-user:test-password@test-db-server/test-db"
        assert str(settings.SQLALCHEMY_DATABASE_URI) == expected_url
    
    def test_testing_database_url(self, monkeypatch):
        """Test that SQLite is used for testing."""
        # Setup testing environment
        monkeypatch.setenv("TESTING", "1")
        monkeypatch.setenv("ENVIRONMENT", "testing")
        
        # Load settings
        settings = Settings()
        
        # In test mode, we should be using SQLite
        assert "sqlite+aiosqlite" in str(settings.SQLALCHEMY_DATABASE_URI)
    
    def test_cors_settings(self, monkeypatch):
        """Test CORS origins settings parsing."""
        # Test comma-separated string format
        monkeypatch.setenv("BACKEND_CORS_ORIGINS", "http://localhost,https://example.com")
        
        settings = Settings()
        assert len(settings.BACKEND_CORS_ORIGINS) == 2
        assert "http://localhost" in settings.BACKEND_CORS_ORIGINS
        assert "https://example.com" in settings.BACKEND_CORS_ORIGINS
        
        # Test list format
        monkeypatch.setenv("BACKEND_CORS_ORIGINS", '["http://localhost:8000", "https://api.example.com"]')
        
        settings = Settings()
        assert len(settings.BACKEND_CORS_ORIGINS) == 2
        assert "http://localhost:8000" in settings.BACKEND_CORS_ORIGINS
        assert "https://api.example.com" in settings.BACKEND_CORS_ORIGINS