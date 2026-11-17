import os

os.environ.setdefault('SECRET_KEY', 'test-secret-key')

import pytest
from sqlalchemy import select

from app import create_app
from config import TestConfig
from extensions import db
from models import User
from seed.loader import seed_all


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        seed_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def sign_up(client, email='ada@example.com', name='Ada Lovelace', password='password123', confirm=None):
    return client.post('/signup', data={
        'name': name, 'email': email, 'password': password,
        'confirm': password if confirm is None else confirm,
    })

def get_user(email='ada@example.com'):
    return db.session.scalar(select(User).where(User.email == email))