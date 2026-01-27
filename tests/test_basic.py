import pytest
import azure_teambots
from azure_teambots.version import __version__

def test_version():
    assert __version__ is not None
    assert isinstance(__version__, str)

def test_import():
    assert azure_teambots is not None
