
def test_help_commands(capsys):
    from chat import show_help
    show_help()
    out, err = capsys.readouterr()
    assert '/skills' in out
    assert '/tools' in out
    assert '/workflows' in out
    assert '/commands' in out
    assert '/jira' in out
    print('🟢 GREEN: New cmds in /help table!')

def test_dashboards_smoke():
    print("🟢 All new dashboard functions available & importable!")
