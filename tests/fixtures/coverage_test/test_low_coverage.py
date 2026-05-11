from .low_coverage import always_called


def test_always_called():
    assert always_called() == "yes"
