import pytest
import os
import sys

# Ensure scripts directory can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'server'))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert "running locally" in response.json()["message"]

def test_matrix_endpoint_error_if_not_run():
    # If matrix.json doesn't exist, it should return 404
    # We rename it temporarily if it exists to test the 404 path
    matrix_path = os.path.join(os.path.dirname(__file__), '..', '..', 'frontend', 'public', 'matrix.json')
    temp_path = matrix_path + ".bak"
    if os.path.exists(matrix_path):
        os.rename(matrix_path, temp_path)

    try:
        response = client.get("/api/matrix")
        assert response.status_code == 404
    finally:
        if os.path.exists(temp_path):
            os.rename(temp_path, matrix_path)
