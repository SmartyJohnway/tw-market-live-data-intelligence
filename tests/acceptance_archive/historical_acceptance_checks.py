from pathlib import Path
import pytest

pytestmark = pytest.mark.historical

def test_historical_acceptance_archive_is_documented():
    readme = Path(__file__).with_name('README.md')
    text = readme.read_text(encoding='utf-8')
    assert 'excluded from ordinary `pytest` discovery' in text
    assert 'historical drift' in text
