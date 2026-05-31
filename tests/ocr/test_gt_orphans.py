from pdomain_book_tools.ocr.gt_orphans import GtOrphans


def test_gt_orphans_defaults_empty():
    o = GtOrphans()
    assert o.words == []
    assert o.lines == []
    assert o.paragraphs == []
    assert o.page == []


def test_gt_orphans_with_data():
    o = GtOrphans(words=["foo"], lines=["bar"], paragraphs=["baz"], page=["qux"])
    assert o.words == ["foo"]
    assert o.lines == ["bar"]
    assert o.paragraphs == ["baz"]
    assert o.page == ["qux"]


def test_gt_orphans_is_empty():
    assert GtOrphans().is_empty()
    assert not GtOrphans(words=["x"]).is_empty()
