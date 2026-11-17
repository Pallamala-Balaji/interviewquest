import json

import pytest
from sqlalchemy import select

from extensions import db
from models import Level, Stage, StageProgress
from seed import loader
from seed.loader import seed_stages
from services.progress import complete_stage, ensure_stage_progress, stage_items
from tests.conftest import get_user, sign_up


def sql_world():
    return db.session.scalar(select(Level).where(Level.slug == 'sql'))


def stage(order_no, slug='sql'):
    level = db.session.scalar(select(Level).where(Level.slug == slug))
    return db.session.scalar(select(Stage).where(Stage.level_id == level.id, Stage.order_no == order_no))


def statuses(user, slug='sql'):
    level = db.session.scalar(select(Level).where(Level.slug == slug))
    return [progress.status for _, progress in stage_items(user, level)]


def pass_through(user, last, slug='sql'):
    """Pass every stage from the start up to and including order number `last`."""
    for order_no in range(1, last + 1):
        item = stage(order_no, slug)
        complete_stage(user, item, score=90 if item.kind != 'stage' else None)


def start(client):
    sign_up(client)
    return get_user()


def test_sql_world_has_stages_and_two_bosses(app):
    items = db.session.scalars(select(Stage).where(Stage.level_id == sql_world().id).order_by(Stage.order_no)).all()
    assert len(items) == 14
    assert [i.order_no for i in items] == list(range(1, 15))
    assert sum(1 for i in items if i.kind == 'stage') == 12
    assert items[6].kind == 'mini_boss' and items[13].kind == 'main_boss'


def test_stage_seed_is_safe_to_run_twice(app):
    assert seed_stages() == {'added': 0, 'updated': 14, 'retired': 0}


def test_stage_seed_rejects_an_unknown_world(app, tmp_path, monkeypatch):
    bad = [dict(json.loads(loader.STAGES_FILE.read_text(encoding='utf-8'))[0], level='nowhere')]
    path = tmp_path / 'stages.json'
    path.write_text(json.dumps(bad), encoding='utf-8')
    monkeypatch.setattr(loader, 'STAGES_FILE', path)
    with pytest.raises(ValueError):
        seed_stages()


def test_stage_seed_can_swap_two_numbers(app, tmp_path, monkeypatch):
    items = json.loads(loader.STAGES_FILE.read_text(encoding='utf-8'))
    items[0]['order_no'], items[1]['order_no'] = items[1]['order_no'], items[0]['order_no']
    path = tmp_path / 'stages.json'
    path.write_text(json.dumps(items), encoding='utf-8')
    monkeypatch.setattr(loader, 'STAGES_FILE', path)
    seed_stages()
    assert stage(2).slug == 'sql-empty-shelf' and stage(1).slug == 'sql-wanted-poster'


def test_only_the_first_stage_is_open_at_first(client):
    user = start(client)
    assert statuses(user) == ['unlocked'] + ['locked'] * 13


def test_a_locked_stage_is_refused(client):
    start(client)
    refused = client.get('/level/sql/stage/2')
    assert refused.status_code == 302 and refused.headers['Location'].endswith('/level/sql')
    assert client.get('/level/sql/stage/1').status_code == 200


def test_unknown_stage_is_404(client):
    start(client)
    assert client.get('/level/sql/stage/99').status_code == 404


def test_a_stage_in_a_locked_world_is_refused(client):
    start(client)
    refused = client.get('/level/python/stage/1')
    assert refused.status_code == 302 and refused.headers['Location'].endswith('/map')


def test_the_world_page_draws_every_stage(client):
    start(client)
    html = client.get('/level/sql').data.decode()
    assert html.count("class='node") == 14
    assert html.count("class='banner'") == 3
    assert 'Stage 1: The Empty Shelf, open' in html


def test_passing_a_stage_opens_the_next_one(client):
    user = start(client)
    assert complete_stage(user, stage(1)) is True
    assert statuses(user)[:3] == ['completed', 'unlocked', 'locked']
    assert db.session.get(StageProgress, (user.id, stage(1).id)).stars == 3


def test_stars_are_checked_and_never_go_down(client):
    user = start(client)
    for bad in (0, 4, True, '3'):
        with pytest.raises(ValueError):
            complete_stage(user, stage(1), stars=bad)
    complete_stage(user, stage(1), stars=3)
    complete_stage(user, stage(1), stars=1)
    assert db.session.get(StageProgress, (user.id, stage(1).id)).stars == 3


def test_a_locked_stage_cannot_be_passed(client):
    user = start(client)
    with pytest.raises(PermissionError):
        complete_stage(user, stage(2))


def test_the_mini_boss_needs_a_score_and_a_pass(client):
    user = start(client)
    pass_through(user, 6)
    mini = stage(7)
    assert statuses(user)[6] == 'unlocked'
    for bad in (None, -1, 101, 80.5, True):
        with pytest.raises(ValueError):
            complete_stage(user, mini, score=bad)
    assert complete_stage(user, mini, score=79) is False
    assert statuses(user)[7] == 'locked'
    assert complete_stage(user, mini, score=80) is True
    assert statuses(user)[7] == 'unlocked'
    assert db.session.get(StageProgress, (user.id, mini.id)).stars == 1


def test_boss_stars_follow_the_score(client):
    user = start(client)
    pass_through(user, 6)
    complete_stage(user, stage(7), score=100)
    assert db.session.get(StageProgress, (user.id, stage(7).id)).stars == 3


def test_beating_the_main_boss_clears_the_world_and_opens_the_next(client):
    user = start(client)
    pass_through(user, 13)
    assert complete_stage(user, stage(14), score=85) is True
    assert client.get('/level/sql/outro').status_code == 200
    html = client.get('/map').data.decode()
    assert 'Cleared, best 85' in html
    assert client.get('/level/python').status_code == 200


def test_a_failed_main_boss_does_not_clear_the_world(client):
    user = start(client)
    pass_through(user, 13)
    assert complete_stage(user, stage(14), score=60) is False
    assert client.get('/level/python').status_code == 302


def test_the_map_shows_stage_progress(client):
    user = start(client)
    pass_through(user, 5)
    html = client.get('/map').data.decode()
    assert '5 of 12 stages' in html


def test_a_retired_stage_does_not_trap_the_player(client):
    user = start(client)
    complete_stage(user, stage(1))
    stage(2).is_active = False
    db.session.commit()
    assert ensure_stage_progress(user, sql_world()) is True
    level_items = stage_items(user, sql_world())
    assert [p.status for _, p in level_items][:2] == ['completed', 'unlocked']
    assert level_items[1][0].order_no == 3