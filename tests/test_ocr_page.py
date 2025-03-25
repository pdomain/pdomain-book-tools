import pd_book_tools.ocr as ocr
import pd_book_tools.geometry as geometry


def test_page_initialization(sample_page):
    assert sample_page.width == 100
    assert sample_page.height == 200
    assert sample_page.page_index == 1
    assert len(sample_page.items) == 2
    assert sample_page.page_labels == ["labelpage1"]
    assert isinstance(sample_page.bounding_box, geometry.BoundingBox)


def test_page_text(sample_page):
    text = sample_page.text
    assert isinstance(text, str)
    assert "word1 word2\nword3 word4\n\nword5 word6\n\nword7 word8\n" in text


def test_page_words(sample_page):
    words = sample_page.words()
    assert isinstance(words, list)
    assert all(isinstance(word, ocr.Word) for word in words)


def test_page_lines(sample_page):
    lines = sample_page.lines()
    assert isinstance(lines, list)
    assert all(isinstance(line, ocr.Block) for line in lines)


def test_page_to_dict(sample_page):
    page_dict = sample_page.to_dict()
    assert isinstance(page_dict, dict)
    assert "items" in page_dict
    assert "width" in page_dict
    assert "height" in page_dict
    assert "page_index" in page_dict
    assert "bounding_box" in page_dict


def test_page_from_dict(sample_page):
    page_dict = sample_page.to_dict()
    print(page_dict)
    new_page = ocr.Page.from_dict(page_dict)
    assert new_page.width == sample_page.width
    assert new_page.height == sample_page.height
    assert new_page.page_index == sample_page.page_index
    assert len(new_page.items) == len(sample_page.items)
