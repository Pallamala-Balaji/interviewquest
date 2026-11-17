import os

import click

from seed.loader import seed_all


def register_commands(app):
    @app.cli.command('seed')
    def seed_command():
        """Load or update worlds and stages from the seed files."""
        result = seed_all()
        click.echo('Worlds: {added} added, {updated} updated, {retired} retired'.format(**result['levels']))
        click.echo('Stages: {added} added, {updated} updated, {retired} retired'.format(**result['stages']))

    @app.cli.command('dev-complete')
    @click.argument('email')
    @click.argument('world_slug')
    @click.argument('order_no', type=int)
    @click.option('--score', type=int, default=90, show_default=True, help='Score used for boss stages.')
    def dev_complete(email, world_slug, order_no, score):
        """Development only: mark one stage as passed. It stands in for the game until Phase 4 and 6."""
        if os.environ.get('APP_ENV') == 'production':
            raise click.ClickException('This command is not available in production.')

        from sqlalchemy import select

        from extensions import db
        from models import Level, Stage, User
        from services.progress import complete_stage, ensure_progress, ensure_stage_progress

        user = db.session.scalar(select(User).where(User.email == email.lower()))
        level = db.session.scalar(select(Level).where(Level.slug == world_slug))
        if user is None or level is None:
            raise click.ClickException('Unknown email or world.')
        stage = db.session.scalar(select(Stage).where(Stage.level_id == level.id, Stage.order_no == order_no))
        if stage is None:
            raise click.ClickException('That world has no stage with that number.')
        ensure_progress(user)
        ensure_stage_progress(user, level)
        try:
            passed = complete_stage(user, stage, score=score)
        except (PermissionError, ValueError) as error:
            raise click.ClickException(str(error))
        click.echo('{} "{}": {}'.format(stage.kind, stage.title, 'passed' if passed else 'not passed'))