"""
backend/tests/test_config.py

Test configuration loader and settings defaults.
"""

from app.config import Settings


def test_settings_default_values():
    settings = Settings()
    assert settings.APP_NAME == "IP-SAKTI Sahayak API"
    assert "http://localhost:5173" in settings.CORS_ORIGINS
    assert settings.JWT_ALGORITHM == "HS256"


def test_settings_cors_string_parsing():
    settings = Settings(CORS_ORIGINS="http://example.com, http://test.com")
    assert "http://example.com" in settings.CORS_ORIGINS
    assert "http://test.com" in settings.CORS_ORIGINS
