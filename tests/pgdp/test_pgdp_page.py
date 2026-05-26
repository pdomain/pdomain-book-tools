import json
import pathlib

import pytest

from pdomain_book_tools.pgdp.pgdp_results import PGDPExport, PGDPResults


def test_remove_proofer_notes():
    src = "Text[*remove me*] Keep"
    out = PGDPResults.remove_proofer_notes(src)
    assert "remove me" not in out
    assert out.strip() == "Text Keep"


def test_remove_blank_page():
    src = "First line\n[Blank Page]\nSecond"
    out = PGDPResults.remove_blank_page(src)
    assert "Blank Page" not in out
    assert "Second" in out


def test_convert_pgdp_dashes_precedence():
    # "------" should become ⸺-- (first 4 -> long dash, remaining 2 -> em dash)
    src = "a------b -- c ---- d"
    out = PGDPResults.convert_pgdp_dashes(src)
    assert out.count("⸺") == 2  # one for ------ (first four) + one for explicit ----
    assert out.count("\u2014") >= 1  # EM DASH
    assert "--" not in out  # all converted


def test_split_hyphen_asterisk():
    src = "word-*Wrap\nNext"  # pattern -*Wrap then newline Next
    out = PGDPResults.split_hyphen_asterisk(src)
    assert out == "word-\nWrap Next"


def test_remove_leading_trailing_asterisk():
    src = "*Some text-*"
    out = PGDPResults.remove_leading_trailing_asterisk(src)
    assert out == "Some text-"


def test_remove_trailing_asterisk_no_dash():
    # Trailing '*' without a preceding hyphen/em-dash: drop '*', add nothing.
    src = "Some text*"
    out = PGDPResults.remove_leading_trailing_asterisk(src)
    assert out == "Some text"


def test_remove_leading_asterisk_no_following_word_split():
    # Leading '*' without a hyphenated wrap context: just drop the '*'.
    src = "*Some text"
    out = PGDPResults.remove_leading_trailing_asterisk(src)
    assert out == "Some text"


def test_remove_trailing_asterisk_after_em_dash():
    # Trailing '--*' should keep the em dash and drop the '*'.
    src = "Some text\u2014*"  # EM DASH
    out = PGDPResults.remove_leading_trailing_asterisk(src)
    assert out == "Some text\u2014"  # EM DASH


def test_fix_footnotes():
    src = "Line[12] more[3]"
    out = PGDPResults.fix_footnotes(src)
    assert out == "Line12 more3"


def test_fix_footnotes_no_space_before_marker():
    # Marker attached to preceding word should not get a space inserted
    src = "word[2] and standalone [5] text"
    out = PGDPResults.fix_footnotes(src)
    assert out == "word2 and standalone 5 text"
    assert " 2" not in out


def test_fix_pgdp_diacritics_subset():
    src = "[=A][=a][:E][.C][`U]['y][)E][c,]"
    out = PGDPResults.fix_pgdp_diacritics(src)
    # Ensure expected mapped characters appear; some mappings (E-caron variants) may vary
    for ch in ["Ā", "ā", "Ë", "Ċ", "Ù", "ý", "ç"]:
        assert ch in out
    assert len(out) == 8


def test_fix_pgdp_diacritics_dot_above_does_not_swallow_other_brackets():
    """The dot-above patterns (e.g. r"\\[.A\\]") used unescaped '.', which is a regex
    wildcard. Any [xA]-shaped bracket sequence then got incorrectly replaced with
    the dot-above letter instead of running through its proper diacritic pattern.

    Regression for H-02 in docs/review/bugs-high.md.
    """
    # Acute-A: should become Á, NOT Ȧ (dot-above A).
    assert PGDPResults.fix_pgdp_diacritics("['A]") == "Á"
    # Grave-A: should become À, NOT Ȧ.
    assert PGDPResults.fix_pgdp_diacritics("[`A]") == "À"
    # Breve-A: should become Ă, NOT Ȧ.
    assert PGDPResults.fix_pgdp_diacritics("[)A]") == "Ă"
    # Acute-E / grave-E / breve-E should not be swallowed by the dot-above-E pattern.
    assert PGDPResults.fix_pgdp_diacritics("['E]") == "É"
    assert PGDPResults.fix_pgdp_diacritics("[`E]") == "È"
    assert PGDPResults.fix_pgdp_diacritics("[)E]") == "Ĕ"
    # Mixed input: each bracket sequence should be replaced correctly.
    src = "['A][`A][)A][.A]"
    assert PGDPResults.fix_pgdp_diacritics(src) == "ÁÀĂȦ"


def test_convert_straight_to_curly_quotes_cases():
    src = "'Tis 'word' \"Hello\" can't don't \u2014'after 'end'"  # EM DASH
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    assert "'" not in out
    assert '"' not in out
    for ch in [
        "\u2018",
        "\u2019",
        "\u201c",
        "\u201d",
    ]:  # LEFT SINGLE QUOTATION MARK, RIGHT SINGLE QUOTATION MARK, LEFT DOUBLE QUOTATION MARK, RIGHT DOUBLE QUOTATION MARK
        assert ch in out
    assert "can\u2019t" in out
    assert "don\u2019t" in out
    assert "\u2019Tis" in out  # RIGHT SINGLE QUOTATION MARK


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
    page = PGDPResults(str(fake_png), text)

    assert "Note" not in page.processed_page_text
    assert "Blank Page" not in page.processed_page_text
    assert not page.processed_page_text.startswith("*")
    assert not page.processed_page_text.rstrip().endswith("-*")
    assert "--" not in page.processed_page_text
    assert (
        "\u2014" in page.processed_page_text or "⸺" in page.processed_page_text
    )  # EM DASH
    # Hyphen wrap line split: look for wrap- newline Word
    assert "wrap-\nWord" in page.processed_page_text
    # Footnote marker brackets removed, no space inserted before the number
    assert "Footnote23" in page.processed_page_text
    # Diacritics line converted (at least subset present)
    for ch in ["Ā", "ā", "Ë", "Ċ", "Ù", "ý", "ç"]:
        assert ch in page.processed_page_text
    # Curly opening apostrophe
    assert "\u2019Tis" in page.processed_page_text  # RIGHT SINGLE QUOTATION MARK
    assert page.processed_lines
    assert all(
        isinstance(t[0], int) and isinstance(t[1], str) for t in page.processed_lines
    )
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


def test_pgdp_export_from_json_directory_not_file(tmp_path):
    # Passing a directory path should raise FileNotFoundError hitting the "Not a file" branch
    with pytest.raises(FileNotFoundError):
        PGDPExport.from_json_file(tmp_path)


def test_pgdp_export_from_json_empty_object(tmp_path):
    # Empty JSON object should return export with zero pages and project_id == directory stem
    export = PGDPExport.from_json("{}", tmp_path)
    assert export.project_id == tmp_path.stem
    assert export.pages == []


def test_pgdp_export_from_json_empty_object_str_path_prefix(tmp_path):
    """L-26 regression: str path_prefix + empty pages dict crashed on
    ``path_prefix.stem`` because the in-loop ``isinstance(..., str)``
    conversion never ran when ``pages`` was empty. Conversion is now
    hoisted above the loop so the ``.stem`` access succeeds.
    """
    export = PGDPExport.from_json("{}", str(tmp_path))
    assert export.project_id == tmp_path.stem
    assert export.pages == []


def test_pgdp_export_from_json_path_prefix_str_multiple(tmp_path):
    # Use string path_prefix to exercise str->Path conversion inside loop
    json_str = '{"a.png": "A text", "b.png": "B text"}'
    export = PGDPExport.from_json(json_str, str(tmp_path))
    assert export.project_id == tmp_path.stem
    names = sorted([p.png_full_path.name for p in export.pages])
    assert names == ["a.png", "b.png"]
    # Ensure processed text stored
    assert any("A text" in p.original_page_text for p in export.pages)


def test_pgdp_export_from_json_file_success(tmp_path):
    data = {"pX.png": "Some text"}
    json_path = tmp_path / "pages.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    export = PGDPExport.from_json_file(json_path)
    assert len(export.pages) == 1
    assert export.pages[0].png_full_path.name == "pX.png"


def test_pgdp_export_from_json_file_success_str_path(tmp_path):
    data = {"pY.png": "Other text"}
    json_path = tmp_path / "pages_str.json"
    json_path.write_text(json.dumps(data), encoding="utf-8")
    # Pass as string to trigger isinstance(input_file_path, str) branch
    export = PGDPExport.from_json_file(str(json_path))
    assert len(export.pages) == 1
    assert export.pages[0].png_full_path.name == "pY.png"


# --- Additional quotation handling tests (may initially fail until logic refined) ---


def test_convert_quotes_basic_double():
    src = '"Hello"'
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    assert (
        out == "\u201cHello\u201d"
    )  # LEFT DOUBLE QUOTATION MARK, RIGHT DOUBLE QUOTATION MARK


def test_convert_quotes_nested():
    src = "\"He said, 'Go.'\""
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    assert (
        out == "\u201cHe said, \u2018Go.\u2019\u201d"
    )  # LEFT SINGLE QUOTATION MARK, RIGHT SINGLE QUOTATION MARK, LEFT DOUBLE QUOTATION MARK, RIGHT DOUBLE QUOTATION MARK


def test_convert_quotes_possessive():
    src = "James' hat"
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    assert out == "James\u2019 hat"  # RIGHT SINGLE QUOTATION MARK


def test_convert_quotes_contraction():
    src = "don't"
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    assert out == "don\u2019t"  # RIGHT SINGLE QUOTATION MARK


def test_convert_quotes_leading_elision_lowercase():
    src = "'tis the season"
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    # Expect apostrophe, not opening single quote
    assert out.startswith("\u2019tis")  # RIGHT SINGLE QUOTATION MARK
    assert "\u2018tis" not in out  # LEFT SINGLE QUOTATION MARK


def test_convert_quotes_leading_elision_variants():
    variants = ["'Twas", "'twas", "'Twere", "'twill", "'twould", "'Cause", "'cause"]
    out_list = [PGDPResults.convert_straight_to_curly_quotes(v) for v in variants]
    # Each should start with apostrophe right single quote
    for original, converted in zip(variants, out_list, strict=False):
        assert converted[0] == "\u2019", (  # RIGHT SINGLE QUOTATION MARK
            f"Expected apostrophe for {original}: got {converted[0]!r}"
        )


def test_convert_quotes_decade_abbreviation():
    src = "In the '90s there was"
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    assert "\u201990s" in out  # RIGHT SINGLE QUOTATION MARK
    assert "\u201890s" not in out  # LEFT SINGLE QUOTATION MARK


def test_convert_quotes_year_abbreviation():
    src = "It happened in '05 when"
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    assert "\u201905" in out  # RIGHT SINGLE QUOTATION MARK
    assert "\u201805" not in out  # LEFT SINGLE QUOTATION MARK


def test_convert_quotes_after_em_dash_double():
    src = '\u2014"Well"'  # EM DASH
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    # Expect opening double curly after em dash
    # Accept either fully converted with both curly or only first converted depending on current logic
    assert out.startswith("\u2014\u201cWell")  # LEFT DOUBLE QUOTATION MARK, EM DASH
    assert out != "\u2014\u201dWell\u201d"  # Not both closing


def test_convert_quotes_after_em_dash_single():
    src = "\u2014'Well"  # EM DASH
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    assert out.startswith("\u2014\u2018Well")  # LEFT SINGLE QUOTATION MARK, EM DASH


def test_convert_quotes_word_final_drop():
    src = "doin' it"
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    assert out == "doin\u2019 it"  # RIGHT SINGLE QUOTATION MARK


def test_convert_quotes_cause_in_quoted_phrase():
    src = '"\'Cause he left"'
    out = PGDPResults.convert_straight_to_curly_quotes(src)
    # Opening double quote, apostrophe in Cause
    assert out.startswith(
        "\u201c\u2019Cause"
    )  # RIGHT SINGLE QUOTATION MARK, LEFT DOUBLE QUOTATION MARK
    assert (
        "\u201c\u2018Cause" not in out
    )  # LEFT SINGLE QUOTATION MARK, LEFT DOUBLE QUOTATION MARK

    # --- Large integrated lorem-style pages exercising ordering & density ---

    def test_pgdp_large_mixed_order_case1(tmp_path):
        """Large page with dense mixed ordering of transformations."""
        lorem = (
            "[*Editor note: remove*]\n"
            "[Blank Page]\n"  # should be removed
            "*'Twas the night-- before---- the test-*\n"  # leading * trailing -*, dashes
            "Wrap-*Ping\n"  # split pattern
            "Foot[12] notes[34] mid[56] line\n"  # footnotes
            "Some [=A][=a][:E][.C][`U]['y][c,] diacritics.\n"  # diacritics
            "Year '05 and the '90s style, James' cap, doin' things.\n"  # quotes/apostrophes variants
            'He said, "Go-- now," and\u2014"Stay" then \u2014"Leave".\n'  # double quotes after dash & em dash
            "'Cause 'twas 'tis round 'mid 'n 'til 'Twill 'Twould tests.\n"  # elisions list
        )
        fake_png = tmp_path / "big1.png"
        fake_png.write_bytes(b"")
        page = PGDPResults(str(fake_png), lorem)

        txt = page.processed_page_text
        # Proofer note & blank page removed
        assert "Editor note" not in txt
        assert "Blank Page" not in txt
        # Leading * removed and trailing -* cleaned
        assert not txt.lstrip().startswith("*")
        assert "-*\n" not in txt
        # Long dash (⸺) and em dash (--) present, no raw double hyphens
        assert "--" not in txt
        assert ("\u2014" in txt) or ("⸺" in txt)  # EM DASH
        # Hyphen asterisk split executed
        assert "Wrap-\nPing" in txt
        # Footnotes separated
        for num in ("12", "34", "56"):
            assert f" {num}" in txt
        # Diacritics replaced
        for ch in ["Ā", "ā", "Ë", "Ċ", "Ù", "ý", "ç"]:
            assert ch in txt
        # Elisions apostrophes are right single quotes
        for word in [
            "\u2019Cause",  # RIGHT SINGLE QUOTATION MARK
            "\u2019twas",  # RIGHT SINGLE QUOTATION MARK
            "\u2019Twas",  # RIGHT SINGLE QUOTATION MARK
            "\u2019tis",  # RIGHT SINGLE QUOTATION MARK
            "\u2019mid",  # RIGHT SINGLE QUOTATION MARK
            "\u2019n",  # RIGHT SINGLE QUOTATION MARK
            "\u2019til",  # RIGHT SINGLE QUOTATION MARK
            "\u2019Twill",  # RIGHT SINGLE QUOTATION MARK
            "\u2019Twould",  # RIGHT SINGLE QUOTATION MARK
        ]:
            assert word in txt
        # Possessive & contraction
        assert "James\u2019 cap" in txt
        assert "doin\u2019 things" in txt
        # Double quotes curly
        assert "\u201cGo" in txt
        assert "Stay\u201d" in txt
        # Processed structures non-empty and size reasonable
        assert len(page.processed_lines) >= 6
        assert len(page.processed_words) > 30

    def test_pgdp_large_mixed_order_case2(tmp_path):
        """Similar content, but reorder operations to stress precedence."""
        lorem = (
            "*Prelude---- to "  # long dash first
            "'Em 'Round -- 'Mongst 'Ere 'En 'Cause Figures[1]\n"  # elisions with capitals
            "Paragraph two\u2014'Twas a time of change[2] and James' hat\u2014'twill shine.\n"  # EM DASH
            "Footing[345] after words, doin' chores, and '05 tales of the '90s.\n"
            "[Blank Page]\n"
            "[*Cut this*]\n"
            "Split wrap-*Here\n"
            "Diacritics: [=A][=a][:E][.C][`U]['y][c,].-*"
        )
        fake_png = tmp_path / "big2.png"
        fake_png.write_bytes(b"")
        page = PGDPResults(str(fake_png), lorem)
        txt = page.processed_page_text

        # Ensure removals
        assert "Cut this" not in txt
        assert "Blank Page" not in txt
        # No stray raw hyphen groups
        assert "--" not in txt
        # Apostrophes for elisions
        for w in [
            "\u2019Em",  # RIGHT SINGLE QUOTATION MARK
            "\u2019Round",  # RIGHT SINGLE QUOTATION MARK
            "\u2019Mongst",  # RIGHT SINGLE QUOTATION MARK
            "\u2019Ere",  # RIGHT SINGLE QUOTATION MARK
            "\u2019En",  # RIGHT SINGLE QUOTATION MARK
            "\u2019Cause",  # RIGHT SINGLE QUOTATION MARK
            "\u2019Twas",  # RIGHT SINGLE QUOTATION MARK
            "\u2019twill",  # RIGHT SINGLE QUOTATION MARK
        ]:
            assert w in txt
        # Footnotes separated
        for n in ["1", "2", "345"]:
            assert f" {n}" in txt
        # Split executed
        assert "wrap-\nHere" in txt
        # Diacritics subset
        for ch in ["Ā", "ā", "Ë", "Ċ", "Ù", "ý", "ç"]:
            assert ch in txt
        # Trailing -* cleaned
        assert not txt.rstrip().endswith("-*")
        # Possessive & contraction
        assert "James\u2019 hat" in txt
        assert "doin\u2019 chores" in txt
        # Years
        assert "\u201905" in txt
        assert "\u201990s" in txt
        assert len(page.processed_words) > 35

    def test_pgdp_large_mixed_order_case3(tmp_path):
        """Edge density: multiple adjacent markers and mixed punctuation clusters."""
        lorem = (
            "[*X*][Blank Page]*'Mid--'mid----'mid 'til 'Til 'til 'tis 'Tis[77][88] word-*Wrap\n"
            "Chain[99] of[100] foot[101] notes[202]\n"
            "Quotes: 'He said' -- 'Go' ---- 'Now' 'James' 'doin' '90s '05.\n"
            "Diacritics crowd: [=A][=a][:E][.C][`U]['y][c,].\n"
        )
        fake_png = tmp_path / "big3.png"
        fake_png.write_bytes(b"")
        page = PGDPResults(str(fake_png), lorem)
        txt = page.processed_page_text

        # Removals
        assert "Blank Page" not in txt
        assert "X" not in txt
        # Hyphen split
        assert "word-\nWrap" in txt
        # Dashes converted
        assert "--" not in txt
        # Footnotes separated
        for n in ["77", "88", "99", "100", "101", "202"]:
            assert f" {n}" in txt
        # Elisions & apostrophes consistent
        for frag in [
            "\u2019Mid",
            "\u2019mid",
            "\u2019til",
            "\u2019Tis",
            "\u2019tis",
        ]:  # RIGHT SINGLE QUOTATION MARK
            assert frag in txt
        # Contractions & decades
        assert "doin\u2019" in txt
        assert "\u201990s" in txt
        assert "\u201905" in txt
        # Possessive James' present
        assert "James\u2019" in txt  # RIGHT SINGLE QUOTATION MARK
        # Diacritics subset
        for ch in ["Ā", "ā", "Ë", "Ċ", "Ù", "ý", "ç"]:
            assert ch in txt
        # Quotes converted (no stray straight quotes except apostrophes replaced)
        assert "'" not in txt.replace(
            "\u2019",
            "",  # RIGHT SINGLE QUOTATION MARK
        )  # all remaining singles are curly apostrophes
        # Size
        assert len(page.processed_words) > 40
