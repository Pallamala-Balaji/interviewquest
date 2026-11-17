from flask import Blueprint, jsonify, request
from flask_login import current_user

from extensions import db

prefs_bp = Blueprint('prefs', __name__)

THEMES = ('system', 'light', 'dark')
ALLOWED_KEYS = {'theme', 'sound_on'}


@prefs_bp.route('/api/prefs', methods=['POST'])
def save_prefs():
    """Save the player's theme and sound choice. Visitors who are not logged in keep theirs in the browser."""
    if not current_user.is_authenticated:
        return jsonify(error='Log in to save your settings.'), 401

    data = request.get_json(silent=True)
    if not isinstance(data, dict) or not data:
        return jsonify(error='Send a JSON object.'), 400
    if set(data) - ALLOWED_KEYS:
        return jsonify(error='Unknown setting.'), 400

    theme = data.get('theme', current_user.theme)
    sound_on = data.get('sound_on', current_user.sound_on)
    if theme not in THEMES:
        return jsonify(error='theme must be system, light, or dark.'), 400
    if not isinstance(sound_on, bool):
        return jsonify(error='sound_on must be true or false.'), 400

    current_user.theme = theme
    current_user.sound_on = sound_on
    db.session.commit()
    return jsonify(ok=True, theme=theme, sound_on=sound_on)