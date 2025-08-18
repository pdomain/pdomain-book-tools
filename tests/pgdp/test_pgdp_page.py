import json
import pathlib

import pytest

from pd_book_tools.pgdp.pgdp_results import PGDPPage, PGDPExport


def test_remove_proofer_notes():
    src = "Text[*remove me*] Keep"
    out = PGDPPage.remove_proofer_notes(src)
    assert "remove me" not in out
    assert out.strip() == "Text Keep"


def test_remove_blank_page():
    src = "First line\n[Blank Page]\nSecond"
    out = PGDPPage.remove_blank_page(src)
    assert "Blank Page" not in out
    assert "Second" in out


def test_convert_pgdp_dashes_precedence():
    # "------" should become ⸺— (first 4 -> long dash, remaining 2 -> em dash)
    src = "a------b -- c ---- d"
    out = PGDPPage.convert_pgdp_dashes(src)
    assert out.count("⸺") == 2  # one for ------ (first four) + one for explicit ----
    assert out.count("—") >= 1
    assert "--" not in out  # all converted


def test_split_hyphen_asterisk():
    src = "word-*Wrap\nNext"  # pattern -*Wrap then newline Next
    out = PGDPPage.split_hyphen_asterisk(src)
    assert out == "word-\nWrap Next"


def test_remove_leading_trailing_asterisk():
    src = "*Some text-*"
    out = PGDPPage.remove_leading_trailing_asterisk(src)
    assert out == "Some text-"


def test_fix_footnotes():
    src = "Line[12] more[3]"
    out = PGDPPage.fix_footnotes(src)
    assert out == "Line 12 more 3"


def test_fix_pgdp_diacritics_subset():
    src = "[=A][=a][:E][.C][`U]['y][)E][c,]"
    out = PGDPPage.fix_pgdp_diacritics(src)
    # Ensure expected mapped characters appear; some mappings (E-caron variants) may vary
    for ch in ["Ā", "ā", "Ë", "Ċ", "Ù", "ý", "ç"]:
        assert ch in out
    assert len(out) == 8


def test_convert_straight_to_curly_quotes_cases():
    src = "'Tis 'word' \"Hello\" can't don't —'after 'end'"
    out = PGDPPage.convert_straight_to_curly_quotes(src)
    assert "'" not in out
    assert '"' not in out
    for ch in ["‘", "’", "“", "”"]:
        assert ch in out
    assert "can’t" in out and "don’t" in out
    assert "’Tis" in out


def test_pgdp_page_process_integration(tmp_path):
    text = (
        "[*Note*]\n"
        "[Blank Page]\n"
        "*'Tis -- a test----*\n"
    "Hyphen wrap-*Word\n"
        "Footnote[23]\n"
        "[=A][=a][:E][.C][`U]['y][)E][c,]-*"
    )
    fake_png = tmp_path / "page1.png"
    fake_png.write_bytes(b"")
    page = PGDPPage(str(fake_png), text)

    assert "Note" not in page.processed_page_text
    assert "Blank Page" not in page.processed_page_text
    assert not page.processed_page_text.startswith("*")
    assert not page.processed_page_text.rstrip().endswith("-*")
    assert "--" not in page.processed_page_text
    assert "—" in page.processed_page_text or "⸺" in page.processed_page_text
    # Hyphen wrap line split: look for wrap- newline Word
    assert "wrap-\nWord" in page.processed_page_text
    # Footnote number separated
    assert "Footnote 23" in page.processed_page_text
    # Diacritics line converted (at least subset present)
    for ch in ["Ā", "ā", "Ë", "Ċ", "Ù", "ý", "ç"]:
        assert ch in page.processed_page_text
    # Curly opening apostrophe
    assert "’Tis" in page.processed_page_text
    assert page.processed_lines
    assert all(isinstance(t[0], int) and isinstance(t[1], str) for t in page.processed_lines)
    assert page.processed_words
    assert all(len(t) == 3 for t in page.processed_words)


def test_pgdp_export_from_json(tmp_path):
    data = {"p1.png": "Line one", "p2.png": "Second line"}
    json_path = tmp_path / "export.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    export = PGDPExport.from_json_file(json_path)
    assert export.project_id == tmp_path.stem
    assert len(export.pages) == 2
    png_paths = {pathlib.Path(p.png_full_path).name for p in export.pages}
    assert png_paths == {"p1.png", "p2.png"}


def test_pgdp_export_from_json_missing_file(tmp_path):
    missing = tmp_path / "nope.json"
    with pytest.raises(FileNotFoundError):
        PGDPExport.from_json_file(missing)
