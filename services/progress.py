from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from extensions import db
from models import Level, LevelProgress, Stage, StageProgress


def active_levels():
    return db.session.scalars(
        select(Level).where(Level.is_active.is_(True)).order_by(Level.order_no)
    ).all()


def next_level(level):
    return db.session.scalar(
        select(Level)
        .where(Level.is_active.is_(True), Level.order_no > level.order_no)
        .order_by(Level.order_no)
        .limit(1)
    )


def ensure_progress(user):
    """Create missing progress rows and repair locks that should be open.

    Safe to call many times. A level is open when the level before it is completed,
    and the first active level is always open.
    """
    existing = {
        row.level_id: row
        for row in db.session.scalars(
            select(LevelProgress).where(LevelProgress.user_id == user.id)
        )
    }
    previous_done = True          # the first active level starts unlocked
    changed = False
    for level in active_levels():
        row = existing.get(level.id)
        if row is None:
            status = 'unlocked' if previous_done else 'locked'
            db.session.add(LevelProgress(user_id=user.id, level_id=level.id, status=status))
            changed = True
            previous_done = False
        else:
            if row.status == 'locked' and previous_done:
                row.status = 'unlocked'    # repair, for example after a level was retired
                changed = True
            previous_done = row.status == 'completed'
    if changed:
        try:
            db.session.commit()
        except IntegrityError:    # another request created the rows first
            db.session.rollback()
    return changed


def unlock_next(user, level, score):
    """Record a boss score. Called only by the boss engine (Phase 6).

    Returns True when the level was passed (and the next one unlocked).
    """
    if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError('score must be a whole number from 0 to 100')

    progress = db.session.get(LevelProgress, (user.id, level.id))
    if progress is None or progress.status == 'locked':
        raise PermissionError('this level is locked for this user')

    progress.best_score = max(progress.best_score, score)
    passed = score >= level.pass_mark
    if passed:
        progress.status = 'completed'
        following = next_level(level)
        if following is not None:
            nxt = db.session.get(LevelProgress, (user.id, following.id))
            if nxt is None:
                db.session.add(LevelProgress(user_id=user.id, level_id=following.id, status='unlocked'))
            elif nxt.status == 'locked':
                nxt.status = 'unlocked'
    db.session.commit()
    return passed


# ---------------------------------------------------------------- stages inside a world

def level_stages(level):
    return db.session.scalars(
        select(Stage).where(Stage.level_id == level.id, Stage.is_active.is_(True)).order_by(Stage.order_no)
    ).all()


def ensure_stage_progress(user, level):
    """Create missing stage rows for one world and repair locks that should be open.

    A stage is open when the one before it is completed. The first stage is open when the
    world itself is open. Safe to call many times.
    """
    world = db.session.get(LevelProgress, (user.id, level.id))
    previous_done = world is not None and world.status != 'locked'
    existing = {
        row.stage_id: row
        for row in db.session.scalars(
            select(StageProgress)
            .join(Stage, Stage.id == StageProgress.stage_id)
            .where(StageProgress.user_id == user.id, Stage.level_id == level.id)
        )
    }
    changed = False
    for stage in level_stages(level):
        row = existing.get(stage.id)
        if row is None:
            status = 'unlocked' if previous_done else 'locked'
            db.session.add(StageProgress(user_id=user.id, stage_id=stage.id, status=status))
            changed = True
            previous_done = False
        else:
            if row.status == 'locked' and previous_done:
                row.status = 'unlocked'
                changed = True
            previous_done = row.status == 'completed'
    if changed:
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
    return changed


def stage_items(user, level):
    """(stage, progress) pairs in order, creating missing rows first."""
    ensure_stage_progress(user, level)
    return db.session.execute(
        select(Stage, StageProgress)
        .join(StageProgress, (StageProgress.stage_id == Stage.id) & (StageProgress.user_id == user.id))
        .where(Stage.level_id == level.id, Stage.is_active.is_(True))
        .order_by(Stage.order_no)
    ).all()


def stars_for_score(score):
    return 3 if score == 100 else 2 if score >= 90 else 1


def complete_stage(user, stage, score=None, stars=None):
    """Record a result for one stage. Called by the game engines (Phase 4 and Phase 6).

    A normal stage passes when the player solves it (stars 1 to 3, default 3).
    A mini boss or main boss needs a score from 0 to 100 and passes at the world's pass mark.
    Passing opens the next stage. Passing the main boss completes the world and opens the next one.
    Returns True when the stage was passed.
    """
    level = db.session.get(Level, stage.level_id)
    ensure_stage_progress(user, level)
    progress = db.session.get(StageProgress, (user.id, stage.id))
    if progress is None or progress.status == 'locked':
        raise PermissionError('this stage is locked for this user')

    is_boss = stage.kind in ('mini_boss', 'main_boss')
    if is_boss:
        if isinstance(score, bool) or not isinstance(score, int) or not 0 <= score <= 100:
            raise ValueError('a boss needs a whole-number score from 0 to 100')
        progress.best_score = max(progress.best_score, score)
        passed = score >= level.pass_mark
        earned = stars_for_score(score)
    else:
        if stars is None:
            stars = 3
        if isinstance(stars, bool) or not isinstance(stars, int) or not 1 <= stars <= 3:
            raise ValueError('stars must be 1, 2, or 3')
        passed = True
        earned = stars

    if passed:
        progress.status = 'completed'
        progress.stars = max(progress.stars, earned)
        following = db.session.scalar(
            select(Stage)
            .where(Stage.level_id == stage.level_id, Stage.is_active.is_(True), Stage.order_no > stage.order_no)
            .order_by(Stage.order_no)
            .limit(1)
        )
        if following is not None:
            nxt = db.session.get(StageProgress, (user.id, following.id))
            if nxt is None:
                db.session.add(StageProgress(user_id=user.id, stage_id=following.id, status='unlocked'))
            elif nxt.status == 'locked':
                nxt.status = 'unlocked'

    if passed and stage.kind == 'main_boss':
        db.session.flush()
        unlock_next(user, level, score)      # completes the world and opens the next one
        return True

    db.session.commit()
    return passed