from tests.conftest import sign_up


def test_seed_command_reports_both_files(app):
    result = app.test_cli_runner().invoke(args=['seed'])
    assert result.exit_code == 0
    assert 'Worlds: 0 added, 10 updated, 0 retired' in result.output
    assert 'Stages: 0 added, 14 updated, 0 retired' in result.output


def test_dev_complete_passes_a_stage(client, app):
    sign_up(client)
    runner = app.test_cli_runner()
    result = runner.invoke(args=['dev-complete', 'ada@example.com', 'sql', '1'])
    assert result.exit_code == 0 and 'passed' in result.output
    locked = runner.invoke(args=['dev-complete', 'ada@example.com', 'sql', '5'])
    assert locked.exit_code != 0 and 'locked' in locked.output


def test_dev_complete_is_blocked_in_production(client, app, monkeypatch):
    sign_up(client)
    monkeypatch.setenv('APP_ENV', 'production')
    result = app.test_cli_runner().invoke(args=['dev-complete', 'ada@example.com', 'sql', '1'])
    assert result.exit_code != 0 and 'not available in production' in result.output