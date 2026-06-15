from pdomain_book_tools.image_processing.grayscale_pipeline.config import (
    ClaheConfig,
    Converter,
    FlattenConfig,
    GrayscaleConfig,
)


def test_default_config_is_plain_luma():
    cfg = GrayscaleConfig()
    assert cfg.converter is Converter.luma
    assert cfg.flatten.enabled is False
    assert cfg.clahe.enabled is False
    assert cfg.output_range is None


def test_config_roundtrips_through_dict():
    cfg = GrayscaleConfig(
        flatten=FlattenConfig(enabled=True, radius=64, strength=1.0),
        converter=Converter.best_channel,
        channel="green",
        clahe=ClaheConfig(enabled=True, clip_limit=2.0, tile_grid=8),
    )
    assert GrayscaleConfig.from_dict(cfg.to_dict()) == cfg


def test_from_dict_rejects_unknown_converter():
    import pytest

    with pytest.raises(ValueError):
        GrayscaleConfig.from_dict({"converter": "bogus"})
