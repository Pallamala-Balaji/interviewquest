import json

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Level, LevelProgress, User
from seed import loader
from seed.loader import seed_levels
from services.progress import ensure_progress, unlock_next
from tests.conftest import get_user, sign_up


def world(slug):
    return db.session.scalar(select(Level).where(Level.slug == slug))


def statuses(user):
    rows = db.session.execute(
        select(Level.order_no, LevelProgress.status)
        .join(LevelProgress, LevelProgress.level_id == Level.id)
        .where(LevelProgress.user_id == user.id)
        .order_by(Level.order_no)
    ).all()
    return [status for _, status in rows]


def write_json(tmp_path, name, items):
    path = tmp_path / name
    path.write_text(json.dumps(items), encoding='utf-8')
    return path


def test_seed_is_safe_to_run_twice(app):
    assert db.session.query(Level).count() == 10
    assert seed_levels() == {'added': 0, 'updated': 10, 'retired': 0}
    world('sql').title = 'Changed by mistake'
    db.session.commit()
    seed_levels()
    assert world('sql').title == 'SQL'


def test_new_user_gets_progress_rows(client):
    sign_up(client)
    assert statuses(get_user()) == ['unlocked'] + ['locked'] * 9


def test_map_needs_login(client):
    response = client.get('/map')
    assert response.status_code == 302
    assert '/login' in response.headers['Location']


def test_locked_world_is_refused(client):
    sign_up(client)
    locked = client.get('/level/python')
    assert locked.status_code == 302
    assert locked.headers['Location'].endswith('/map')
    assert client.get('/level/sql').status_code == 200


def test_unknown_world_is_404(client):
    sign_up(client)
    assert client.get('/level/not-a-world').status_code == 404


def test_old_user_without_rows_is_repaired(client):
    user = User(name='Old User', email='old@example.com', hero_name='Old User', avatar_id='1')
    user.set_password('password123')
    db.session.add(user)
    db.session.commit()
    client.post('/login', data={'email': 'old@example.com', 'password': 'password123'})
    assert client.get('/map').status_code == 200
    assert statuses(get_user('old@example.com'))[0] == 'unlocked'


def test_unlock_next_needs_the_pass_mark(client):
    sign_up(client)
    user = get_user()
    assert unlock_next(user, world('sql'), 79) is False
    assert statuses(user)[:2] == ['unlocked', 'locked']
    assert unlock_next(user, world('sql'), 80) is True
    assert statuses(user)[:3] == ['completed', 'unlocked', 'locked']


def test_best_score_never_goes_down(client):
    sign_up(client)
    user = get_user()
    unlock_next(user, world('sql'), 90)
    unlock_next(user, world('sql'), 40)
    assert db.session.get(LevelProgress, (user.id, world('sql').id)).best_score == 90


def test_locked_world_cannot_be_scored(client):
    sign_up(client)
    with pytest.raises(PermissionError):
        unlock_next(get_user(), world('python'), 100)


def test_bad_scores_are_rejected(client):
    sign_up(client)
    user = get_user()
    for bad in (-1, 101, 80.5, '90', True, False):
        with pytest.raises(ValueError):
            unlock_next(user, world('sql'), bad)


def test_outro_needs_a_cleared_world(client):
    sign_up(client)
    assert client.get('/level/sql/outro').status_code == 302
    unlock_next(get_user(), world('sql'), 85)
    assert client.get('/level/sql/outro').status_code == 200
    assert client.get('/level/python').status_code == 200


def test_duplicate_progress_row_is_blocked(client):
    sign_up(client)
    db.session.add(LevelProgress(user_id=get_user().id, level_id=world('sql').id, status='unlocked'))
    with pytest.raises(IntegrityError):
        db.session.commit()
    db.session.rollback()


def test_ensure_progress_adds_rows_for_a_new_world(client):
    sign_up(client)
    user = get_user()
    unlock_next(user, world('sql'), 100)
    db.session.add(Level(slug='bonus', order_no=11, title='Bonus', world='Bonus Isle', area='Bonus',
                         engine='quiz', story_intro='x', story_outro='y', boss_name='Boss'))
    db.session.commit()
    assert ensure_progress(user) is True
    assert statuses(user)[-1] == 'locked'
    assert ensure_progress(user) is False


def test_locks_are_repaired_when_a_world_is_retired(client):
    sign_up(client)
    user = get_user()
    first, second, third = world('sql'), world('python'), world('dsa')

    first.is_active = False
    db.session.commit()
    assert client.get('/map').status_code == 200
    assert db.session.get(LevelProgress, (user.id, second.id)).status == 'unlocked'
    first.is_active = True
    db.session.commit()

    unlock_next(user, first, 90)
    second.is_active = False
    db.session.commit()
    assert ensure_progress(user) is True
    assert db.session.get(LevelProgress, (user.id, third.id)).status == 'unlocked'


def test_seed_can_swap_two_world_numbers(app, tmp_path, monkeypatch):
    items = json.loads(loader.LEVELS_FILE.read_text(encoding='utf-8'))
    items[0]['order_no'], items[1]['order_no'] = items[1]['order_no'], items[0]['order_no']
    monkeypatch.setattr(loader, 'LEVELS_FILE', write_json(tmp_path, 'levels.json', items))
    seed_levels()
    assert world('sql').order_no == 2 and world('python').order_no == 1


def test_new_world_can_reuse_a_retired_number(app, tmp_path, monkeypatch):
    items = [i for i in json.loads(loader.LEVELS_FILE.read_text(encoding='utf-8')) if i['slug'] != 'dragon']
    items.append(dict(items[0], slug='new-final', order_no=10, title='New Final'))
    monkeypatch.setattr(loader, 'LEVELS_FILE', write_json(tmp_path, 'levels.json', items))
    assert seed_levels() == {'added': 1, 'updated': 9, 'retired': 1}
    assert world('new-final').order_no == 10 and world('dragon').is_active is False