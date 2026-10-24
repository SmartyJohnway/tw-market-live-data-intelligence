"""Exact committed source admission must fail closed before packaging."""
import pytest

from scripts.release_validation_source import ENTRY, exact_release_validation_source


SHA = 'a' * 40
TREE = 'b' * 40


def git_fixture(*, dirty=False, head=SHA, tree=TREE):
    calls = []
    def git(*args):
        calls.append(args)
        if args[0] == 'status':
            return b'?? unexpected.txt' if dirty else b''
        if args[:2] == ('rev-parse', 'HEAD'):
            return head.encode()
        if args[:2] == ('rev-parse', 'HEAD^{tree}'):
            return tree.encode()
        if args == ('merge-base', '--is-ancestor', ENTRY, SHA):
            return b''
        raise AssertionError(args)
    return git, calls


def test_exact_clean_source_requires_authorized_ancestry():
    git, calls = git_fixture()
    assert exact_release_validation_source(git, SHA, TREE) == (SHA, TREE)
    assert calls[-1] == ('merge-base', '--is-ancestor', ENTRY, SHA)


@pytest.mark.parametrize('commit,tree', [(None, TREE), (SHA, None), ('main', TREE), ('A'*40, TREE), (SHA, '../tree')])
def test_moving_or_malformed_identity_rejected_before_git(commit, tree):
    git, calls = git_fixture()
    with pytest.raises(ValueError):
        exact_release_validation_source(git, commit, tree)
    assert not calls


@pytest.mark.parametrize('kwargs', [{'dirty': True}, {'head': 'c'*40}, {'tree': 'c'*40}])
def test_dirty_or_mismatched_source_rejected(kwargs):
    git, calls = git_fixture(**kwargs)
    with pytest.raises(ValueError):
        exact_release_validation_source(git, SHA, TREE)
    assert not any(call[0] == 'merge-base' for call in calls)
