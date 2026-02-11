import pytest
from app import app
import json

@pytest.fixture
def client():
    """Create a test client for the app."""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_status_code(client):
    """Test that the index endpoint returns 200."""
    response = client.get('/')
    assert response.status_code == 200

def test_index_content(client):
    """Test that the index endpoint returns expected JSON structure."""
    response = client.get('/')
    data = json.loads(response.data)
    
    # Check top-level keys
    assert 'service' in data
    assert 'system' in data
    assert 'runtime' in data
    assert 'request' in data
    
    # Check specific values
    assert data['service']['name'] == 'devops-info-service'

def test_health_status_code(client):
    """Test that the health endpoint returns 200."""
    response = client.get('/health')
    assert response.status_code == 200

def test_health_content(client):
    """Test that the health endpoint returns healthy status."""
    response = client.get('/health')
    data = json.loads(response.data)
    
    assert data['status'] == 'healthy'
    assert 'timestamp' in data
    assert 'uptime_seconds' in data

def test_index_endpoints(client):
    """Test that the index endpoint lists available endpoints."""
    response = client.get('/')
    data = json.loads(response.data)
    
    assert 'endpoints' in data
    assert isinstance(data['endpoints'], list)
    paths = [ep['path'] for ep in data['endpoints']]
    assert '/' in paths
    assert '/health' in paths

def test_health_response_types(client):
    """Test that health endpoint returns correct data types."""
    response = client.get('/health')
    data = json.loads(response.data)
    
    assert isinstance(data['uptime_seconds'], int)
    assert data['uptime_seconds'] >= 0
    assert isinstance(data['timestamp'], str)
