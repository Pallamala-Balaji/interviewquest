import json
from pathlib import Path

from sqlalchemy import select

from extensions import db
from models import Level

LEVELS_FILE = Path(__file__).parent / 'levels.json'
FIELDS = ['order_no', 'title', 'world', 'area', 'engine', 'pass_mark',
          'story_intro', 'story_outro', 'boss_name']
LEVEL_OPTIONAL = ['guide', 'key_name']


def seed_levels():
    """Add new levels, update existing ones by slug, retire levels removed from the file."""
    items = json.loads(LEVELS_FILE.read_text(encoding='utf-8'))
    new_numbers = {item['slug']: item['order_no'] for item in items}
    existing = {level.slug: level for level in db.session.scalars(select(Level))}

    retired = 0
    for slug, level in existing.items():
        if slug not in new_numbers:
            if level.is_active:
                level.is_active = False
                retired += 1
            level.order_no = -level.id
        elif level.order_no != new_numbers[slug]:
            level.order_no = -level.id
    db.session.flush()

    added = updated = 0
    for item in items:
        level = existing.get(item['slug'])
        if level is None:
            level = Level(slug=item['slug'])
            db.session.add(level)
            added += 1
        else:
            updated += 1
        for field in FIELDS:
            setattr(level, field, item[field])
        for field in LEVEL_OPTIONAL:
            setattr(level, field, item.get(field))
        level.is_active = True

    db.session.commit()
    return {'added': added, 'updated': updated, 'retired': retired}


STAGES_FILE = Path(__file__).parent / 'stages.json'
STAGE_FIELDS = ['order_no', 'kind', 'title', 'concept', 'story']
STAGE_OPTIONAL = ['banner']


def seed_stages():
    """Add new stages, update existing ones by slug, retire stages removed from the file."""
    from models import Stage

    items = json.loads(STAGES_FILE.read_text(encoding='utf-8'))
    levels = {level.slug: level for level in db.session.scalars(select(Level))}
    existing = {stage.slug: stage for stage in db.session.scalars(select(Stage))}

    wanted = {}
    for item in items:
        level = levels.get(item['level'])
        if level is None:
            raise ValueError("stage '{}' points at an unknown level '{}'".format(item['slug'], item['level']))
        wanted[item['slug']] = (level, item)

    retired = 0
    for slug, stage in existing.items():
        if slug not in wanted:
            if stage.is_active:
                stage.is_active = False
                retired += 1
            stage.order_no = -stage.id
        else:
            level, item = wanted[slug]
            if stage.order_no != item['order_no'] or stage.level_id != level.id:
                stage.order_no = -stage.id
    db.session.flush()

    added = updated = 0
    for slug, (level, item) in wanted.items():
        stage = existing.get(slug)
        if stage is None:
            stage = Stage(slug=slug, level_id=level.id)
            db.session.add(stage)
            added += 1
        else:
            stage.level_id = level.id
            updated += 1
        for field in STAGE_FIELDS:
            setattr(stage, field, item[field])
        for field in STAGE_OPTIONAL:
            setattr(stage, field, item.get(field))
        stage.is_active = True

    db.session.commit()
    return {'added': added, 'updated': updated, 'retired': retired}


def seed_all():
    """Load worlds first, then their stages."""
    return {'levels': seed_levels(), 'stages': seed_stages()}