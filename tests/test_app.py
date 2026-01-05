import pytest
from run import create_app


@pytest.mark.unit
def test_app_creation():
    """Test that the app can be created."""
    app = create_app()
    assert app is not None
    assert app.name == 'run'


@pytest.mark.unit
def test_app_config(app):
    """Test app configuration in test mode."""
    assert app.config['TESTING'] is True


@pytest.mark.unit
def test_app_has_blueprint(app):
    """Test that the main blueprint is registered."""
    assert 'main' in app.blueprints
