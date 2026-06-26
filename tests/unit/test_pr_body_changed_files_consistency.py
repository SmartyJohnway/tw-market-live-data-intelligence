import sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/'scripts'))

from scripts.check_pr_body_changed_files_consistency import check_pr_body_changed_files_consistency as chk
def body(lines): return '## Actual changed files\n'+'\n'.join(f'- `{x}`' for x in lines)+'\n## Validation\n'
def test_exact_match_pass(): assert chk(body(['a.py']),['a.py']).ok
def test_extra_nonexistent_file_fail(): assert not chk(body(['a.py','b.py']),['a.py']).ok
def test_missing_changed_file_warning(): assert chk(body(['a.py']),['a.py','c.py']).warnings
def test_no_section_fail(): assert not chk('none',['a']).ok
def test_duplicate_file_entry_warning(): assert chk(body(['a.py','a.py']),['a.py']).warnings
def test_markdown_fenced_block_parsing(): assert chk('## Actual changed files\n```\na.py\n```\n',['a.py']).ok
