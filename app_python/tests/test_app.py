import pytest
import json
from unittest.mock import patch, MagicMock
from app import app

@pytest.fixture
def client():
    """
    Fixture to setup the Flask test client.
    Sets testing mode to True to ensure exceptions are propagated 
    or handled by error handlers correctly.
    """
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_status_code(client):
    """
    Test that the index endpoint returns 200 OK.
    Verifies the basic availability of the service.
    """
    response = client.get('/')
    assert response.status_code == 200

def test_index_structure_and_mock(client):
    """
    Test index content structure and mock system calls.
    Demonstrates mocking external dependencies (socket, platform) which are
    'external' to the application logic.
    """
    expected_hostname = 'mock-hostname'
    expected_platform = 'MockOS'

    # Mocking socket and platform to ensure tests don't depend on the actual system
    with patch('socket.gethostname', return_value=expected_hostname), \
         patch('platform.system', return_value=expected_platform):
        
        response = client.get('/')
        data = json.loads(response.data)
        
        # Assertion: Structure presence
        assert 'service' in data
        assert 'system' in data
        assert 'runtime' in data
        
        # Assertion: Mocked values (Expected vs Actual)
        assert data['system']['hostname'] == expected_hostname, "Hostname matches mocked value"
        assert data['system']['platform'] == expected_platform, "Platform matches mocked value"
        
        # Assertion: Data Types
        assert isinstance(data['runtime']['uptime_seconds'], int), "Uptime should be an integer"
        assert isinstance(data['service']['version'], str), "Version should be a string"

def test_health_check(client):
    """
    Test health endpoint status and logic.
    """
    response = client.get('/health')
    assert response.status_code == 200
    
    data = json.loads(response.data)
    
    # Assertions
    assert data['status'] == 'healthy'
    assert isinstance(data['uptime_seconds'], int)
    assert 'timestamp' in data

def test_404_not_found(client):
    """
    Test error handling for non-existent routes.
    Verifies that the application handles 404 errors gracefully.
    """
    response = client.get('/non-existent-route-random-String')
    
    # Assertion: Correct HTTP status code for missing resource
    assert response.status_code == 404
    
    data = json.loads(response.data)
    assert data['error'] == 'Not Found'

def test_500_internal_error(client):
    """
    Test internal server error handling.
    Mocks a core component to raise an Exception to simulate a crash.
    """
    with patch('socket.gethostname', side_effect=Exception("Simulated IO Error")):
        # By default in TESTING mode, Flask propagates exceptions.
        # We turn it off for this specific test block to catch the 500 error handler response.
        app.config['PROPAGATE_EXCEPTIONS'] = False 
        
        response = client.get('/')
        
        assert response.status_code == 500
        data = json.loads(response.data)
        assert data['error'] == 'Internal Server Error'
        
        # Restore configuration
        app.config['PROPAGATE_EXCEPTIONS'] = True
