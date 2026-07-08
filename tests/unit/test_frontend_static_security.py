from pathlib import Path

INDEX = Path("frontend/public/index.html")


def _script() -> str:
    return INDEX.read_text(encoding="utf-8")


def test_matrix_error_details_are_not_interpolated_into_innerhtml():
    html = _script()
    assert "Error details: ${e.message}" not in html
    assert "renderMatrixLoadError(e)" in html
    assert "textContent = text" in html


def test_matrix_rows_use_dom_textcontent_for_dynamic_values():
    html = _script()
    assert "data.results.forEach(row =>" in html
    assert "document.createElement('tr')" in html
    assert "appendText(sourceCell, 'strong', row.source || '')" in html
    assert "appendText(tr, 'td', row.delay_status || 'N/A')" in html
    assert "html += `" not in html
    assert "matrix-container').innerHTML" not in html
