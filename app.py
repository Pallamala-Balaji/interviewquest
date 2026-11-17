from flask import Flask
from config import Config
from constants import AVATARS, AVATAR_INFO
from extensions import csrf, db, login_manager, migrate
from commands import register_commands


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    import models  # noqa: F401

    from routes.auth import auth_bp
    from routes.levels import levels_bp
    from routes.main import main_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(levels_bp)
    register_commands(app)

    app.jinja_env.globals['avatar'] = lambda avatar_id: AVATARS.get(str(avatar_id), AVATARS["1"])
    app.jinja_env.globals['avatar_info'] = AVATAR_INFO

    return app