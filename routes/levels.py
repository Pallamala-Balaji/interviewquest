from functools import wraps

from flask import Blueprint, abort, flash, redirect, render_template, url_for
from flask_login import current_user, login_required
from sqlalchemy import func, select

from extensions import db
from models import Level, LevelProgress, Stage, StageProgress
from services.progress import ensure_progress, ensure_stage_progress, next_level, stage_items
from services.stagemap import build_map, build_world_map

levels_bp = Blueprint('levels', __name__)


def require_unlocked(view):
    """Load the world by slug and refuse the request if it is locked for this user.

    Put it under @login_required. The view receives (level, progress).
    """
    @wraps(view)
    def wrapper(slug, *args, **kwargs):
        level = db.session.scalar(
            select(Level).where(Level.slug == slug, Level.is_active.is_(True))
        )
        if level is None:
            abort(404)
        ensure_progress(current_user)
        progress = db.session.get(LevelProgress, (current_user.id, level.id))
        if progress is None or progress.status == 'locked':
            flash('That world is still locked. Beat the main boss of the world before it to open it.', 'error')
            return redirect(url_for('levels.level_map'))
        return view(level, progress, *args, **kwargs)
    return wrapper


def require_stage_unlocked(view):
    """Put it under @require_unlocked. The view receives (level, progress, stage, stage_progress)."""
    @wraps(view)
    def wrapper(level, progress, order_no, *args, **kwargs):
        stage = db.session.scalar(
            select(Stage).where(Stage.level_id == level.id, Stage.order_no == order_no, Stage.is_active.is_(True))
        )
        if stage is None:
            abort(404)
        ensure_stage_progress(current_user, level)
        stage_progress = db.session.get(StageProgress, (current_user.id, stage.id))
        if stage_progress is None or stage_progress.status == 'locked':
            flash('That stage is still locked. Finish the one before it first.', 'error')
            return redirect(url_for('levels.level_hub', slug=level.slug))
        return view(level, progress, stage, stage_progress, *args, **kwargs)
    return wrapper


def stage_counts(user):
    """How many normal stages exist in each world, and how many this user has cleared."""
    base = (Stage.is_active.is_(True), Stage.kind == 'stage')
    totals = dict(db.session.execute(
        select(Stage.level_id, func.count()).where(*base).group_by(Stage.level_id)
    ).all())
    done = dict(db.session.execute(
        select(Stage.level_id, func.count())
        .join(StageProgress, StageProgress.stage_id == Stage.id)
        .where(*base, StageProgress.user_id == user.id, StageProgress.status == 'completed')
        .group_by(Stage.level_id)
    ).all())
    return totals, done


@levels_bp.route('/map')
@login_required
def level_map():
    ensure_progress(current_user)
    rows = db.session.execute(
        select(Level, LevelProgress)
        .join(LevelProgress, (LevelProgress.level_id == Level.id) & (LevelProgress.user_id == current_user.id))
        .where(Level.is_active.is_(True))
        .order_by(Level.order_no)
    ).all()
    totals, done = stage_counts(current_user)
    cleared = sum(1 for _, progress in rows if progress.status == 'completed')
    return render_template(
        'map.html', world_map=build_world_map(rows, totals, done), cleared=cleared, total=len(rows),
    )


@levels_bp.route('/level/<slug>')
@login_required
@require_unlocked
def level_hub(level, progress):
    items = stage_items(current_user, level)
    normal = [(stage, sp) for stage, sp in items if stage.kind == 'stage']
    return render_template(
        'level.html', level=level, progress=progress, stage_map=build_map(items),
        total=len(normal), done=sum(1 for _, sp in normal if sp.status == 'completed'),
        stars=sum(sp.stars for _, sp in items),
    )


@levels_bp.route('/level/<slug>/stage/<int:order_no>')
@login_required
@require_unlocked
@require_stage_unlocked
def stage_page(level, progress, stage, stage_progress):
    stage_no = None
    if stage.kind == 'stage':
        stage_no = db.session.scalar(
            select(func.count()).select_from(Stage).where(
                Stage.level_id == level.id, Stage.is_active.is_(True),
                Stage.kind == 'stage', Stage.order_no <= stage.order_no)
        )
    return render_template('stage.html', level=level, stage=stage, stage_progress=stage_progress, stage_no=stage_no)


@levels_bp.route('/level/<slug>/outro')
@login_required
@require_unlocked
def level_outro(level, progress):
    if progress.status != 'completed':
        flash('Beat the main boss to read how this world ends.', 'error')
        return redirect(url_for('levels.level_hub', slug=level.slug))
    return render_template('level_outro.html', level=level, following=next_level(level))