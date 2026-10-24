"""Exact-source admission for the Owner-authorized L7-A2 validation build."""
from __future__ import annotations
import re

ENTRY = '0e903ba042df7fed63f2c0ccd1c82dd5a28b62b5'


def exact_release_validation_source(git, commit: str, tree: str) -> tuple[str, str]:
    if not all(isinstance(x,str) and re.fullmatch(r'[0-9a-f]{40}',x) for x in (commit,tree)):
        raise ValueError('release validation requires exact commit and tree')
    if git('status','--porcelain','--untracked-files=all').strip():
        raise ValueError('release validation requires clean committed source')
    if git('rev-parse','HEAD').decode().strip()!=commit or git('rev-parse','HEAD^{tree}').decode().strip()!=tree:
        raise ValueError('L7_A2_FRESH_CLONE_IDENTITY_MISMATCH')
    git('merge-base','--is-ancestor',ENTRY,commit)
    # Task entry authorization is checked before implementation. A repeatable
    # validation build admits an explicit immutable source, including later
    # reviewed merge commits; it never selects/fetches a moving main implicitly.
    return commit,tree
