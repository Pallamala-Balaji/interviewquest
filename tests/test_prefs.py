import re

import pytest

from config import TestConfig
from app import create_app
from extensions import db
from tests.conftest import get_user, sign_up


def post_prefs(client, payload):
    return client.post('/api/prefs', json=payload)


def test_prefs_need_login(client):
    response = post_prefs(client, {'theme': 'dark'})
    assert response.status_code == 401


def test_prefs_save_theme_and_sound(client):
    sign_up(client)
    response = post_prefs(client, {'theme': 'dark', 'sound_on': False})
    assert response.status_code == 200
    assert response.get_json() == {'ok': True, 'theme': 'dark', 'sound_on': False}
    user = get_user()
    assert user.theme == 'dark' and user.sound_on is False


def test_prefs_can_change_one_setting_at_a_time(client):
    sign_up(client)
    post_prefs(client, {'theme': 'light'})
    post_prefs(client, {'sound_on': False})
    user = get_user()
    assert user.theme == 'light' and user.sound_on is False


@pytest.mark.parametrize('payload', [
    {'theme': 'purple'}, {'sound_on': 'yes'}, {'sound_on': 1}, {'colour': 'red'}, {}, [], 'dark',
])
def test_prefs_reject_bad_input(client, payload):
    sign_up(client)
    assert post_prefs(client, payload).status_code == 400


def test_prefs_reject_a_body_that_is_not_json(client):
    sign_up(client)
    assert client.post('/api/prefs', data='theme=dark').status_code == 400


def test_saved_theme_is_drawn_into_the_page(client):
    sign_up(client)
    assert "data-theme='system'" in client.get('/').data.decode()
    post_prefs(client, {'theme': 'dark', 'sound_on': False})
    html = client.get('/').data.decode()
    assert "data-theme='dark'" in html
    assert "data-sound='0'" in html


def test_visitors_get_no_server_theme(client):
    html = client.get('/').data.decode()
    assert "<html lang='en'>" in html
    assert "data-logged-in='0'" in html


def test_every_page_has_the_settings_panel_and_scripts(client):
    sign_up(client)
    for url in ('/', '/map', '/level/sql', '/level/sql/stage/1', '/hero'):
        html = client.get(url).data.decode()
        assert "class='settings'" in html, url
        for name in ('theme-init', 'iq', 'sound', 'narrate', 'settings'):
            assert 'js/{}.js'.format(name) in html, (url, name)


def test_scenes_have_a_listen_button(client):
    sign_up(client)
    assert "class='listen'" in client.get('/level/sql').data.decode()
    assert "data-target='#scene-text'" in client.get('/level/sql/stage/1').data.decode()


@pytest.mark.parametrize('name', ['theme-init', 'iq', 'sound', 'narrate', 'settings', 'ui', 'world', 'hero', 'home'])
def test_the_script_files_are_served(client, name):
    assert client.get('/static/js/{}.js'.format(name)).status_code == 200


class CsrfConfig(TestConfig):
    WTF_CSRF_ENABLED = True


def test_prefs_require_the_csrf_token():
    app = create_app(CsrfConfig)
    with app.app_context():
        db.create_all()
        client = app.test_client()
        page = client.get('/signup').data.decode()
        token = re.search(r"name='csrf-token' content='([^']+)'", page).group(1)
        client.post('/signup', data={'name': 'Ada L', 'email': 'ada@example.com', 'password': 'password123',
                                     'confirm': 'password123', 'csrf_token': token})
        token = re.search(r"name='csrf-token' content='([^']+)'", client.get('/').data.decode()).group(1)
        assert client.post('/api/prefs', json={'theme': 'dark'}).status_code == 400
        ok = client.post('/api/prefs', json={'theme': 'dark'}, headers={'X-CSRFToken': token})
        assert ok.status_code == 200
        db.session.remove()
        db.drop_all()