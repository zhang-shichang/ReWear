"""Pytest configuration and shared fixtures."""
import os
import sys
import tempfile
from pathlib import Path

import pytest
from flask import Flask

# Add rewear_app to path so imports work
rewear_app_path = os.path.join(os.path.dirname(__file__), '..', 'rewear_app')
if rewear_app_path not in sys.path:
    sys.path.insert(0, rewear_app_path)

# Now import after path is set
from app import db, app as flask_app


@pytest.fixture
def app():
    """Create application for testing."""
    # Use in-memory SQLite database for tests
    flask_app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    flask_app.config['TESTING'] = True
    flask_app.config['WTF_CSRF_ENABLED'] = False
    
    with flask_app.app_context():
        db.create_all()
        yield flask_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client for making requests."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner for testing CLI commands."""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Database session for tests."""
    with app.app_context():
        yield db.session


@pytest.fixture
def user_data():
    """Sample user data for testing."""
    return {
        'email': 'test@example.com',
        'password': 'testpassword123',
        'username': 'testuser'
    }


@pytest.fixture
def registered_user(client, user_data):
    """Create and register a test user."""
    response = client.post('/auth/register', json=user_data)
    assert response.status_code == 201
    return response.json['user']


@pytest.fixture
def authenticated_client(client, user_data, registered_user):
    """Create a client with authenticated user session."""
    # Login the user
    response = client.post('/auth/login', json={
        'email': user_data['email'],
        'password': user_data['password']
    })
    assert response.status_code == 200
    return client
