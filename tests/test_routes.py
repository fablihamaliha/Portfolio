import pytest
from unittest.mock import patch, MagicMock


@pytest.mark.unit
def test_home_route_status(client):
    """Test that the home route returns 200."""
    # Mock the weather API call
    mock_response = MagicMock()
    mock_response.json.return_value = {
        'location': {'name': 'San Francisco'},
        'current': {
            'temp_c': 20,
            'condition': {
                'text': 'Partly cloudy',
                'icon': '//cdn.weatherapi.com/weather/64x64/day/116.png'
            }
        }
    }

    with patch('app.routes.main.requests.get', return_value=mock_response):
        response = client.get('/')
        assert response.status_code == 200


@pytest.mark.unit
def test_journey_route(client):
    """Test that the journey route returns 200."""
    response = client.get('/journey')
    assert response.status_code == 200


@pytest.mark.unit
def test_portfolio_route(client):
    """Test that the portfolio route returns 200."""
    response = client.get('/portfolio')
    assert response.status_code == 200


@pytest.mark.unit
def test_certifications_route(client):
    """Test that the certifications route returns 200."""
    response = client.get('/certifications')
    assert response.status_code == 200


@pytest.mark.unit
def test_contact_route(client):
    """Test that the contact route returns 200."""
    response = client.get('/contact')
    assert response.status_code == 200


@pytest.mark.unit
def test_invalid_route(client):
    """Test that invalid routes return 404."""
    response = client.get('/nonexistent')
    assert response.status_code == 404
