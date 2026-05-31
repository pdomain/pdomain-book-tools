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
    assert not GtOrphans(lines=["x"]).is_empty()
    assert not GtOrphans(paragraphs=["x"]).is_empty()
    assert not GtOrphans(page=["x"]).is_empty()


def test_blob_store_protocol_structural():
    import inspect

    from pdomain_book_tools.ocr.blob_protocol import BlobStoreProtocol

    # Verify the Protocol has the expected method
    assert hasattr(BlobStoreProtocol, "read")
    sig = inspect.signature(BlobStoreProtocol.read)
    params = list(sig.parameters)
    assert "hash" in params
