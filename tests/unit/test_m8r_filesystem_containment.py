from __future__ import annotations
import os, sys
from pathlib import Path
import pytest

pytestmark = [pytest.mark.core, pytest.mark.component_security, pytest.mark.milestone]
from scripts.m8r_filesystem_safety import (
    FilesystemSafetyError,
    atomic_write_text,
    classify_artifact_relative_path,
    safe_destination,
    validate_authorized_root,
)

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
        ('/tmp/x.json','rooted_output_path_forbidden'),
        ('C:/tmp/x.json','absolute_output_path_forbidden'),
        ('C:tmp/x.json','drive_relative_output_path_forbidden'),
        ('//server/share/x.json','unc_output_path_forbidden'),
        ('a\\..\\..\\x.json','path_traversal_forbidden'),
    ]:
        with pytest.raises(FilesystemSafetyError) as exc:
            safe_destination(root, candidate)
        assert code(exc) == expected

def test_prefix_collision_rooted_path_rejected(tmp_path):
    root = tmp_path/'output'
    evil = str(tmp_path/'output-evil'/'file.json')
    with pytest.raises(FilesystemSafetyError) as exc:
        safe_destination(root, evil)
    assert code(exc) == 'rooted_output_path_forbidden'

@pytest.mark.parametrize(
    ('candidate', 'path_class', 'rejection_code'),
    [
        ('/tmp/output-evil/file.json', 'rooted', 'rooted_output_path_forbidden'),
        ('C:/tmp/output-evil/file.json', 'absolute', 'absolute_output_path_forbidden'),
        ('C:tmp/output-evil/file.json', 'drive_relative', 'drive_relative_output_path_forbidden'),
        ('//server/share/output-evil/file.json', 'unc', 'unc_output_path_forbidden'),
    ],
    ids=['posix-rooted', 'windows-drive-absolute', 'windows-drive-relative', 'unc'],
)
def test_prefix_collision_lexical_path_classes_are_explicit(
    candidate, path_class, rejection_code,
):
    classification = classify_artifact_relative_path(candidate)

    assert classification.path_class == path_class
    assert classification.rejection_code == rejection_code
    assert classification.safe_relative is False

def test_nonexistent_safe_leaf_and_nested_parent_are_accepted(tmp_path):
    root = tmp_path/'output'
    dest = safe_destination(root, 'new/leaf/file.json', create_parent=False)
    assert not dest.path.parent.exists()
    assert dest.path.name == 'file.json'
    
    dest_create = safe_destination(root, 'new/leaf/file.json', create_parent=True)
    assert dest_create.path.parent.exists()

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
