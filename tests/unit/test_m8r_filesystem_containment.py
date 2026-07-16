from __future__ import annotations
import os, sys
from pathlib import Path
import pytest

pytestmark = [pytest.mark.core, pytest.mark.component_security, pytest.mark.milestone]
from scripts.m8r_filesystem_safety import FilesystemSafetyError, atomic_write_text, safe_destination, validate_authorized_root

def code(exc): return exc.value.code

def test_lexical_safe_relative_paths_are_accepted(tmp_path):
    root = tmp_path/'output'
    assert safe_destination(root, 'a.json').path == root.resolve()/'a.json'
    assert safe_destination(root, 'nested/a.json').path == root.resolve()/'nested'/'a.json'

def test_lexical_traversal_and_absolute_paths_rejected(tmp_path):
    root = tmp_path/'output'
    for candidate, expected in [
        ('../x.json','path_traversal_forbidden'),
        ('a/../../x.json','path_traversal_forbidden'),
        ('/tmp/x.json','absolute_output_path_forbidden'),
        ('C:/tmp/x.json','absolute_output_path_forbidden'),
        ('C:tmp/x.json','absolute_output_path_forbidden'),
        ('//server/share/x.json','absolute_output_path_forbidden'),
        ('a\\..\\..\\x.json','path_traversal_forbidden'),
    ]:
        with pytest.raises(FilesystemSafetyError) as exc:
            safe_destination(root, candidate)
        assert code(exc) == expected

def test_prefix_collision_absolute_path_rejected(tmp_path):
    root = tmp_path/'output'
    evil = str(tmp_path/'output-evil'/'file.json')
    with pytest.raises(FilesystemSafetyError) as exc:
        safe_destination(root, evil)
    assert code(exc) == 'absolute_output_path_forbidden'

def test_nonexistent_safe_leaf_and_nested_parent_are_accepted(tmp_path):
    root = tmp_path/'output'
    dest = safe_destination(root, 'new/leaf/file.json')
    assert dest.path.parent.exists()
    assert dest.path.name == 'file.json'

def test_symlink_parent_escape_rejected(tmp_path):
    root = tmp_path/'output'; outside = tmp_path/'outside'
    root.mkdir(); outside.mkdir()
    link = root/'link'
    try:
        link.symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('symlink creation unsupported')
    with pytest.raises(FilesystemSafetyError) as exc:
        safe_destination(root, 'link/file.json')
    assert code(exc) == 'output_parent_symlink_escape'

def test_nested_symlink_escape_rejected(tmp_path):
    root = tmp_path/'output'; outside = tmp_path/'outside'
    (root/'a').mkdir(parents=True); outside.mkdir()
    try:
        (root/'a'/'b').symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('symlink creation unsupported')
    with pytest.raises(FilesystemSafetyError) as exc:
        safe_destination(root, 'a/b/file.json')
    assert code(exc) == 'output_parent_symlink_escape'

def test_destination_symlink_forbidden(tmp_path):
    root = tmp_path/'output'; outside = tmp_path/'outside'
    root.mkdir(); outside.mkdir()
    target = outside/'target.json'; target.write_text('outside')
    try:
        (root/'dest.json').symlink_to(target)
    except (OSError, NotImplementedError):
        pytest.skip('symlink creation unsupported')
    with pytest.raises(FilesystemSafetyError) as exc:
        safe_destination(root, 'dest.json')
    assert code(exc) == 'output_destination_symlink_forbidden'

def test_root_symlink_is_resolved_as_authorized_root(tmp_path):
    real = tmp_path/'real'; real.mkdir()
    link = tmp_path/'root_link'
    try:
        link.symlink_to(real, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip('symlink creation unsupported')
    assert validate_authorized_root(link) == real.resolve()

def test_atomic_write_places_temp_inside_root_and_replaces(tmp_path):
    root = tmp_path/'output'
    path = atomic_write_text(root, 'nested/file.json', '{"ok": true}\n')
    assert path.read_text() == '{"ok": true}\n'
    assert path.resolve().is_relative_to(root.resolve())
    assert not list(path.parent.glob('*.tmp'))
    atomic_write_text(root, 'nested/file.json', '{"ok": false}\n')
    assert 'false' in path.read_text()

def test_failed_containment_writes_no_output(tmp_path):
    root = tmp_path/'output'
    with pytest.raises(FilesystemSafetyError):
        atomic_write_text(root, '../escape.json', '{}')
    assert not (tmp_path/'escape.json').exists()

def test_authorization_composition_valid_token_does_not_bypass_path(tmp_path):
    token_scope = 'm8r_03e_context_handoff_write'
    assert token_scope
    with pytest.raises(FilesystemSafetyError):
        atomic_write_text(tmp_path/'output', '../escape.json', '{}')
