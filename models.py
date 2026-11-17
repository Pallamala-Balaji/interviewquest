import sqlite3
from datetime import datetime, timezone
from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index, UniqueConstraint, event, true
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
class Level(db.Model):
    __tablename__ = 'levels'
    __table_args__ = (
        CheckConstraint('pass_mark BETWEEN 1 AND 100', name='ck_levels_pass_mark'),
    )

    id = db.Column(db.Integer, primary_key=True)
    slug = db.Column(db.String(60), unique=True, nullable=False)
    order_no = db.Column(db.Integer, unique=True, nullable=False)
    title = db.Column(db.String(80), nullable=False)
    world = db.Column(db.String(80), nullable=False)
    area = db.Column(db.String(30), nullable=False)
    engine = db.Column(db.String(20), nullable=False)
    pass_mark = db.Column(db.Integer, nullable=False, default=80)
    story_intro = db.Column(db.Text, nullable=False)
    story_outro = db.Column(db.Text, nullable=False)
    boss_name = db.Column(db.String(60), nullable=False)
    guide = db.Column(db.String(80), nullable=True)
    key_name = db.Column(db.String(60), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=true())



class LevelProgress(db.Model):
    __tablename__ = 'level_progress'
    __table_args__ = (
        CheckConstraint("status IN ('locked', 'unlocked', 'completed')", name='ck_level_progress_status'),
        CheckConstraint('best_score BETWEEN 0 AND 100', name='ck_level_progress_score'),
    )

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id', ondelete='RESTRICT'), primary_key=True)
    status = db.Column(db.String(10), nullable=False, default='locked')
    best_score = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class Stage(db.Model):
    __tablename__ = 'stages'
    __table_args__ = (
        UniqueConstraint('level_id', 'order_no', name='uq_stages_level_order'),
        CheckConstraint("kind IN ('stage', 'mini_boss', 'main_boss')", name='ck_stages_kind'),
    )

    id = db.Column(db.Integer, primary_key=True)
    level_id = db.Column(db.Integer, db.ForeignKey('levels.id', ondelete='RESTRICT'), nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    order_no = db.Column(db.Integer, nullable=False)
    kind = db.Column(db.String(10), nullable=False, default='stage')
    title = db.Column(db.String(80), nullable=False)
    concept = db.Column(db.String(120), nullable=False)
    story = db.Column(db.Text, nullable=False)
    banner = db.Column(db.String(60), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=true())


class StageProgress(db.Model):
    __tablename__ = 'stage_progress'
    __table_args__ = (
        CheckConstraint("status IN ('locked', 'unlocked', 'completed')", name='ck_stage_progress_status'),
        CheckConstraint('best_score BETWEEN 0 AND 100', name='ck_stage_progress_score'),
        CheckConstraint('stars BETWEEN 0 AND 3', name='ck_stage_progress_stars'),
    )

    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey('stages.id', ondelete='RESTRICT'), primary_key=True)
    status = db.Column(db.String(10), nullable=False, default='locked')
    best_score = db.Column(db.Integer, nullable=False, default=0)
    stars = db.Column(db.Integer, nullable=False, default=0)
    updated_at = db.Column(db.DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)