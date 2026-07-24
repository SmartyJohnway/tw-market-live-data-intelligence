from pathlib import Path
def test_package_has_no_network_or_execution_imports():
 text='\n'.join(p.read_text() for p in Path('scripts/m8r_05b_02').glob('*.py'))
 for forbidden in ('requests','httpx','aiohttp','urllib.request','socket','subprocess','run_source','fetch_market') : assert forbidden not in text
