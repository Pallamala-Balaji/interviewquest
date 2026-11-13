import sqlite3
from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index, event
from sqlalchemy.engine import Engine
from werkzeug.security import check_password_hash, generate_password_hash
from extensions import db, login_manager

@event.listens_for(Engine, 'connect')
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    # SQLite ignores foreign keys unless switched on for each connection[cite: 46]
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys = ON')
        cursor.close()

def utcnow():
    return datetime.now(timezone.utc)

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    __table_args__ = (
        CheckConstraint(
            'is_guest OR (email IS NOT NULL AND password_hash IS NOT NULL)',
            name='ck_users_guest_or_full'
        ),
        Index('ix_users_last_active_at', 'last_active_at'),
    )

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=True)  # Empty for guests[cite: 47]
    password_hash = db.Column(db.String(255), nullable=True)      # Empty for guests[cite: 47]
    name = db.Column(db.String(50), nullable=False)
    hero_name = db.Column(db.String(20), nullable=False)
    avatar_id = db.Column(db.String(50), nullable=False, default="1")
    is_guest = db.Column(db.Boolean, nullable=False, default=False)
    timezone = db.Column(db.String(64), nullable=False, default='UTC')
    last_timezone_change_at = db.Column(db.DateTime(timezone=True), nullable=True)
    xp_personal = db.Column(db.Integer, nullable=False, default=0)
    streak = db.Column(db.Integer, nullable=False, default=0)
    last_daily_date = db.Column(db.Date, nullable=True)
    voice_consent_at = db.Column(db.DateTime(timezone=True), nullable=True)
    theme = db.Column(db.String(10), nullable=False, default='system')
    sound_on = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)
    last_active_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return bool(self.password_hash) and check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))