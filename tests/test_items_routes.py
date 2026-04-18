"""Unit tests for items routes."""
import pytest
import json
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'rewear_app'))

from models import Item, db


class TestGetItems:
    """Tests for GET /items route."""

    def test_get_items_unauthenticated(self, client):
        """Test get_items fails when not authenticated."""
        response = client.get('/items')
        assert response.status_code == 401

    def test_get_items_empty(self, client, authenticated_client):
        """Test get_items returns empty list for new user."""
        response = authenticated_client.get('/items')
        assert response.status_code == 200
        assert response.json == []

    def test_get_items_with_items(self, client, authenticated_client, app, user_data):
        """Test get_items returns user's items."""
        with app.app_context():
            from models import User
            user = db.session.scalar(db.select(User).where(User.email == user_data['email']))
            
            item1 = Item(name='Shirt', category='Top', user_id=user.id)
            item2 = Item(name='Jeans', category='Bottom', user_id=user.id)
            db.session.add(item1)
            db.session.add(item2)
            db.session.commit()
        
        response = authenticated_client.get('/items')
        assert response.status_code == 200
        assert len(response.json) == 2

    def test_get_items_excludes_archived(self, client, authenticated_client, app, user_data):
        """Test get_items excludes archived items."""
        from datetime import datetime
        with app.app_context():
            from models import User
            user = db.session.scalar(db.select(User).where(User.email == user_data['email']))
            
            item1 = Item(name='Current Shirt', user_id=user.id)
            item2 = Item(name='Old Shirt', archived_at=datetime.utcnow(), user_id=user.id)
            db.session.add(item1)
            db.session.add(item2)
            db.session.commit()
        
        response = authenticated_client.get('/items')
        assert response.status_code == 200
        assert len(response.json) == 1
        assert response.json[0]['name'] == 'Current Shirt'


class TestCreateItem:
    """Tests for POST /items route."""

    def test_create_item_unauthenticated(self, client):
        """Test create_item fails when not authenticated."""
        response = client.post('/items', json={'name': 'Test Item'})
        assert response.status_code == 401

    def test_create_item_success(self, client, authenticated_client):
        """Test successful item creation."""
        response = authenticated_client.post('/items', json={
            'name': 'Blue Jeans',
            'category': 'Pants',
            'color': 'Blue',
            'brand': 'Levi',
            'cost': 50.00
        })
        
        assert response.status_code == 201
        data = response.json
        assert data['name'] == 'Blue Jeans'
        assert data['category'] == 'Pants'
        assert data['color'] == 'Blue'

    def test_create_item_missing_name(self, client, authenticated_client):
        """Test create_item fails without name."""
        response = authenticated_client.post('/items', json={
            'category': 'Top'
        })
        
        assert response.status_code == 400
        assert 'error' in response.json

    def test_create_item_negative_cost(self, client, authenticated_client):
        """Test create_item fails with negative cost."""
        response = authenticated_client.post('/items', json={
            'name': 'Shirt',
            'cost': -10.00
        })
        
        assert response.status_code == 400
        assert 'error' in response.json

    def test_create_item_invalid_cost(self, client, authenticated_client):
        """Test create_item fails with invalid cost."""
        response = authenticated_client.post('/items', json={
            'name': 'Shirt',
            'cost': 'not_a_number'
        })
        
        assert response.status_code == 400

    def test_create_item_defaults(self, client, authenticated_client):
        """Test item creation with only required fields."""
        response = authenticated_client.post('/items', json={
            'name': 'Minimalist Item'
        })
        
        assert response.status_code == 201
        data = response.json
        assert data['name'] == 'Minimalist Item'
        assert data['category'] == 'Top'  # Default


class TestUpdateItem:
    """Tests for PUT /items/<id> route."""

    def test_update_item_unauthenticated(self, client, app):
        """Test update_item fails when not authenticated."""
        with app.app_context():
            from models import User
            user = User(email='uniqueuser@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()
            item = Item(name='Test', user_id=user.id)
            db.session.add(item)
            db.session.commit()
            item_id = item.id
        
        response = client.put(f'/items/{item_id}', json={'name': 'Updated'})
        assert response.status_code == 401

    def test_update_item_success(self, client, authenticated_client, app, user_data):
        """Test successful item update."""
        with app.app_context():
            from models import User
            user = db.session.scalar(db.select(User).where(User.email == user_data['email']))
            item = Item(name='Original', category='Top', user_id=user.id)
            db.session.add(item)
            db.session.commit()
            item_id = item.id
        
        response = authenticated_client.put(f'/items/{item_id}', json={
            'name': 'Updated Name',
            'category': 'Bottom'
        })
        
        assert response.status_code == 200
        assert response.json['name'] == 'Updated Name'
        assert response.json['category'] == 'Bottom'

    def test_update_item_not_found(self, client, authenticated_client):
        """Test update_item fails with non-existent item."""
        response = authenticated_client.put('/items/99999', json={'name': 'Test'})
        assert response.status_code == 404

    def test_update_item_forbidden(self, client, authenticated_client, app):
        """Test update_item fails for other user's item."""
        with app.app_context():
            from models import User
            other_user = User(email='other@example.com', password_hash='hash')
            db.session.add(other_user)
            db.session.commit()
            
            item = Item(name='Other User Item', user_id=other_user.id)
            db.session.add(item)
            db.session.commit()
            item_id = item.id
        
        response = authenticated_client.put(f'/items/{item_id}', json={'name': 'Hacked'})
        assert response.status_code == 403

    def test_update_item_negative_cost(self, client, authenticated_client, app, user_data):
        """Test update_item fails with negative cost."""
        with app.app_context():
            from models import User
            user = db.session.scalar(db.select(User).where(User.email == user_data['email']))
            item = Item(name='Test', user_id=user.id)
            db.session.add(item)
            db.session.commit()
            item_id = item.id
        
        response = authenticated_client.put(f'/items/{item_id}', json={'cost': -50})
        assert response.status_code == 400


class TestDeleteItem:
    """Tests for DELETE /items/<id> route."""

    def test_delete_item_unauthenticated(self, client, app):
        """Test delete_item fails when not authenticated."""
        with app.app_context():
            from models import User
            user = User(email='uniqueuser2@example.com', password_hash='hash')
            db.session.add(user)
            db.session.commit()
            item = Item(name='Test', user_id=user.id)
            db.session.add(item)
            db.session.commit()
            item_id = item.id
        
        response = client.delete(f'/items/{item_id}')
        assert response.status_code == 401

    def test_delete_item_not_found(self, client, authenticated_client):
        """Test delete_item fails with non-existent item."""
        response = authenticated_client.delete('/items/99999')
        assert response.status_code == 404

    def test_delete_item_forbidden(self, client, authenticated_client, app):
        """Test delete_item fails for other user's item."""
        with app.app_context():
            from models import User
            other_user = User(email='other@example.com', password_hash='hash')
            db.session.add(other_user)
            db.session.commit()
            
            item = Item(name='Other User Item', user_id=other_user.id)
            db.session.add(item)
            db.session.commit()
            item_id = item.id
        
        response = authenticated_client.delete(f'/items/{item_id}')
        assert response.status_code == 403
