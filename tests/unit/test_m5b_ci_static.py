from pathlib import Path
def test_workflows_do_not_execute_live():
    for p in Path('.github/workflows').glob('*.yml'):
        assert '--execute-live' not in p.read_text()
