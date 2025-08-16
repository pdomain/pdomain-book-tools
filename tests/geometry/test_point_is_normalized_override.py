from pd_book_tools.geometry.point import Point

def test_point_initializer_override_true():
    # values outside [0,1] but force normalized
    p = Point(10, 20, is_normalized=True)
    assert p.is_normalized is True


def test_point_initializer_override_false():
    # values inside [0,1] but force pixel
    p = Point(0.5, 0.5, is_normalized=False)
    assert p.is_normalized is False


def test_point_initializer_override_none_defaults():
    # falls back to inference
    p = Point(0.5, 0.5)
    assert p.is_normalized is True
    q = Point(5, 6)
    assert q.is_normalized is False
