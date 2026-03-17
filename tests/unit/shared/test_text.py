"""Tests for shared.text — HTML stripping and table extraction."""

import pathlib

from bank_ingest.shared.text import extract_table_rows, normalize_whitespace, strip_html

_TESTS_DIR = pathlib.Path(__file__).parent.parent.parent
FIXTURE_PATH = _TESTS_DIR / "fixtures" / "bac_transaction_notification.html"


class TestStripHtml:
    """Unit tests for strip_html."""

    def test_strips_simple_tag(self):
        result = strip_html("<p>Hello World</p>")
        assert "Hello World" in result
        assert "<p>" not in result

    def test_strips_nested_tags(self):
        result = strip_html("<div><span>Text</span></div>")
        assert "Text" in result
        assert "<" not in result

    def test_returns_string(self):
        assert isinstance(strip_html("<p>hi</p>"), str)

    def test_empty_html(self):
        result = strip_html("")
        assert result == ""

    def test_plain_text_unchanged(self):
        result = strip_html("No tags here")
        assert result == "No tags here"

    def test_strips_script_tags(self):
        result = strip_html("<script>alert('xss')</script>plain text")
        assert "alert" not in result
        assert "plain text" in result

    def test_strips_style_tags(self):
        result = strip_html("<style>.a { color: red }</style>visible")
        assert "color" not in result
        assert "visible" in result

    def test_collapses_whitespace(self):
        result = strip_html("<p>  hello   world  </p>")
        assert "  " not in result
        assert "hello world" in result

    def test_strips_leading_trailing_whitespace(self):
        result = strip_html("<p>hello</p>")
        assert result == result.strip()

    def test_bac_fixture_contains_merchant(self):
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        result = strip_html(html)
        assert "CLINICA VETERINARIA GU" in result

    def test_bac_fixture_contains_amount(self):
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        result = strip_html(html)
        assert "CRC 10,000.00" in result

    def test_bac_fixture_no_html_tags(self):
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        result = strip_html(html)
        assert "<" not in result
        assert ">" not in result


class TestNormalizeWhitespace:
    """Unit tests for normalize_whitespace."""

    def test_collapses_multiple_spaces(self):
        assert normalize_whitespace("hello   world") == "hello world"

    def test_collapses_tabs(self):
        assert normalize_whitespace("hello\tworld") == "hello world"

    def test_collapses_newlines(self):
        assert normalize_whitespace("hello\nworld") == "hello world"

    def test_strips_leading(self):
        assert normalize_whitespace("   hello") == "hello"

    def test_strips_trailing(self):
        assert normalize_whitespace("hello   ") == "hello"

    def test_empty_string(self):
        assert normalize_whitespace("") == ""

    def test_whitespace_only(self):
        assert normalize_whitespace("   \t\n  ") == ""

    def test_single_word(self):
        assert normalize_whitespace("hello") == "hello"

    def test_mixed_whitespace(self):
        assert normalize_whitespace("  hello  \n\t  world  ") == "hello world"

    def test_returns_string(self):
        assert isinstance(normalize_whitespace("hello"), str)


class TestExtractTableRows:
    """Unit tests for extract_table_rows."""

    def test_simple_two_column_table(self):
        html = """
        <table>
          <tr><td>Label:</td><td>Value</td></tr>
        </table>
        """
        rows = extract_table_rows(html)
        assert ("Label:", "Value") in rows

    def test_multiple_rows(self):
        html = """
        <table>
          <tr><td>A:</td><td>1</td></tr>
          <tr><td>B:</td><td>2</td></tr>
        </table>
        """
        rows = extract_table_rows(html)
        assert ("A:", "1") in rows
        assert ("B:", "2") in rows

    def test_returns_list_of_tuples(self):
        html = "<table><tr><td>X</td><td>Y</td></tr></table>"
        result = extract_table_rows(html)
        assert isinstance(result, list)
        assert all(isinstance(r, tuple) and len(r) == 2 for r in result)

    def test_strips_cell_whitespace(self):
        html = "<table><tr><td>  Label:  </td><td>  Value  </td></tr></table>"
        rows = extract_table_rows(html)
        assert ("Label:", "Value") in rows

    def test_empty_html_returns_empty_list(self):
        assert extract_table_rows("") == []

    def test_no_table_returns_empty_list(self):
        assert extract_table_rows("<p>No table here</p>") == []

    def test_ignores_rows_with_wrong_column_count(self):
        html = """
        <table>
          <tr><td>Only one cell</td></tr>
          <tr><td>Label:</td><td>Value</td></tr>
          <tr><td>Three</td><td>col</td><td>row</td></tr>
        </table>
        """
        rows = extract_table_rows(html)
        assert ("Label:", "Value") in rows
        # Single-cell and three-cell rows should be excluded
        assert all(len(r) == 2 for r in rows)
        assert ("Only one cell", "") not in rows

    def test_bac_fixture_comercio_row(self):
        """BAC fixture has Comercio: -> CLINICA VETERINARIA GU."""
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        rows = extract_table_rows(html)
        assert ("Comercio:", "CLINICA VETERINARIA GU") in rows

    def test_bac_fixture_fecha_row(self):
        """BAC fixture has Fecha: -> Mar 16, 2026, 08:27 (with potential whitespace)."""
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        rows = extract_table_rows(html)
        # Find the Fecha row
        fecha_rows = [r for r in rows if r[0] == "Fecha:"]
        assert len(fecha_rows) == 1
        # Value should be stripped and contain the date
        assert "Mar 16, 2026, 08:27" in fecha_rows[0][1]

    def test_bac_fixture_monto_row(self):
        """BAC fixture has Monto: -> CRC 10,000.00."""
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        rows = extract_table_rows(html)
        monto_rows = [r for r in rows if r[0] == "Monto:"]
        assert len(monto_rows) == 1
        assert "CRC 10,000.00" in monto_rows[0][1]

    def test_bac_fixture_tipo_transaccion_row(self):
        """BAC fixture has Tipo de Transacción: -> COMPRA."""
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        rows = extract_table_rows(html)
        tipo_rows = [r for r in rows if r[0] == "Tipo de Transacción:"]
        assert len(tipo_rows) == 1
        assert tipo_rows[0][1] == "COMPRA"

    def test_bac_fixture_autorizacion_row(self):
        """BAC fixture has Autorización: -> 000000."""
        html = FIXTURE_PATH.read_text(encoding="utf-8")
        rows = extract_table_rows(html)
        auth_rows = [r for r in rows if r[0] == "Autorización:"]
        assert len(auth_rows) == 1
        assert auth_rows[0][1] == "000000"

    def test_nested_tags_in_cells(self):
        """Cell content with nested tags should extract text only."""
        html = "<table><tr><td><p>Label:</p></td><td><p>Value</p></td></tr></table>"
        rows = extract_table_rows(html)
        assert ("Label:", "Value") in rows
