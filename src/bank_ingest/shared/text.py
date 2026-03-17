"""HTML cleanup and text normalization utilities."""
import re

from bs4 import BeautifulSoup, Tag


def strip_html(html: str) -> str:
    """Extract visible text from HTML, stripping all tags.

    Uses BeautifulSoup with the lxml parser. Collapses whitespace
    and strips leading/trailing whitespace from the result.

    Args:
        html: Raw HTML string.

    Returns:
        Plain text with all HTML tags removed and whitespace normalized.
    """
    if not html:
        return ""

    soup = BeautifulSoup(html, "lxml")

    # Remove script and style elements entirely (including their content)
    for element in soup(["script", "style"]):
        element.decompose()

    text = soup.get_text(separator=" ")
    return normalize_whitespace(text)


def normalize_whitespace(text: str) -> str:
    """Collapse multiple whitespace characters into single spaces and strip.

    Args:
        text: Input string that may contain runs of whitespace.

    Returns:
        String with all whitespace runs collapsed to a single space,
        and leading/trailing whitespace removed.
    """
    return re.sub(r"\s+", " ", text).strip()


def extract_table_rows(html: str) -> list[tuple[str, str]]:
    """Extract key-value pairs from HTML table rows.

    BAC emails use tables with 2 columns: a label column and a value column.
    Rows that do not have exactly 2 cells are skipped.

    Example from BAC HTML:
        <tr><td>Comercio:</td><td>CLINICA VETERINARIA GU</td></tr>
        -> ("Comercio:", "CLINICA VETERINARIA GU")

    Args:
        html: Raw HTML string containing one or more tables.

    Returns:
        List of (label, value) tuples with stripped text. Rows with a column
        count other than 2 are excluded.
    """
    if not html:
        return []

    soup = BeautifulSoup(html, "lxml")
    rows: list[tuple[str, str]] = []

    for tr in soup.find_all("tr"):
        if not isinstance(tr, Tag):
            continue

        cells = tr.find_all("td")
        if len(cells) != 2:
            continue

        label = normalize_whitespace(cells[0].get_text())
        value = normalize_whitespace(cells[1].get_text())
        rows.append((label, value))

    return rows
