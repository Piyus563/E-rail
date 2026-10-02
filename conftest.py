"""
conftest.py — pytest entry point for RailSaathi Django test suite.
Configures Django settings and initialises the app registry before
any test module is imported or collected.
"""
import os
import django


def pytest_configure(config):
    """Set DJANGO_SETTINGS_MODULE and call django.setup() before collection."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()
