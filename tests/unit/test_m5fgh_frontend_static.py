from pathlib import Path
def test_frontend_static_uses_m5f_and_safe_dom():
 js=Path('frontend/readonly-preview/m5e-market-context-adapter.js').read_text(); html=Path('frontend/readonly-preview/M5EMarketContextPreview.html').read_text()
 assert 'research/staging/m5f/m5f_canonical_market_context_01/canonical_market_context.json' in js
 assert 'textContent' in js and 'innerHTML' not in js.replace("'<tr><th>Symbol</th><th>Price-like value</th><th>Source</th><th>Authority</th><th>Source date</th><th>Retrieved</th><th>Freshness</th><th>Delay</th></tr>'",'')
 assert 'refresh' not in html.lower(); assert 'historical/stale' in html
