from pathlib import Path
import pytest
from scripts.m8r_filesystem_safety import FilesystemSafetyError, atomic_write_text

pytestmark = [pytest.mark.core, pytest.mark.component_security]

def test_m8r_03e_r2_valid_token_and_valid_path_accepts(tmp_path):
    token_scope = 'm8r_03e_context_handoff_write'
    path = atomic_write_text(tmp_path / 'root', 'ok/result.json', '{"scope":"%s"}' % token_scope)
    assert path.exists()
    assert path.read_text().startswith('{')

def test_m8r_03e_r2_valid_token_and_escaping_path_rejected(tmp_path):
    token_scope = 'm8r_03e_context_handoff_write'
    assert token_scope
    with pytest.raises(FilesystemSafetyError) as exc:
        atomic_write_text(tmp_path / 'root', '../escape.json', '{}')
    assert exc.value.code == 'path_traversal_forbidden'
    assert not (tmp_path / 'escape.json').exists()
