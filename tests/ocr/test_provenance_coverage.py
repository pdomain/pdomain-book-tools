"""Coverage tests for ocr.provenance helpers."""

import pytest

from pd_book_tools.ocr.provenance import (
    UNKNOWN_METADATA_VALUE,
    OCRModelProvenance,
    OCRProvenance,
)


class TestOCRModelProvenance:
    def test_to_dict_minimal(self):
        m = OCRModelProvenance(name="x")
        assert m.to_dict() == {"name": "x"}

    def test_to_dict_full(self):
        m = OCRModelProvenance(name="x", version="1", weights_id="abc")
        assert m.to_dict() == {"name": "x", "version": "1", "weights_id": "abc"}

    def test_from_dict_full(self):
        m = OCRModelProvenance.from_dict({"name": "x", "version": 7, "weights_id": 9})
        assert m.name == "x"
        assert m.version == "7"
        assert m.weights_id == "9"

    def test_from_dict_missing_name(self):
        m = OCRModelProvenance.from_dict({})
        assert m.name == UNKNOWN_METADATA_VALUE

    def test_from_dict_none_version(self):
        m = OCRModelProvenance.from_dict({"name": "x", "version": None})
        assert m.version is None


class TestOCRProvenance:
    def test_to_dict_minimal(self):
        p = OCRProvenance(engine="x")
        d = p.to_dict()
        assert d == {"engine": "x", "models": []}

    def test_to_dict_full(self):
        p = OCRProvenance(
            engine="doctr",
            engine_version="0.8.1",
            models=[OCRModelProvenance(name="m1")],
            config_fingerprint="fp",
        )
        d = p.to_dict()
        assert d["engine"] == "doctr"
        assert d["engine_version"] == "0.8.1"
        assert d["config_fingerprint"] == "fp"
        assert d["models"] == [{"name": "m1"}]

    def test_from_dict_strings_and_dicts(self):
        p = OCRProvenance.from_dict(
            {
                "engine": "doctr",
                "engine_version": "0.8.1",
                "models": [
                    "m1",
                    {"model": "m2", "version": 2, "weights_id": 5},
                    {"foo": "bar"},  # missing name, ignored
                    "",  # empty string, ignored
                ],
                "config_fingerprint": "fp",
            }
        )
        assert p.engine == "doctr"
        assert p.engine_version == "0.8.1"
        assert p.config_fingerprint == "fp"
        assert len(p.models) == 2
        assert p.models[0].name == "m1"
        assert p.models[1].name == "m2"
        assert p.models[1].version == "2"
        assert p.models[1].weights_id == "5"

    def test_from_dict_models_not_list(self):
        p = OCRProvenance.from_dict({"engine": "x", "models": "not a list"})
        # L-15: ``models`` is a tuple for real frozen-dataclass immutability.
        assert p.models == ()

    def test_from_dict_engine_default(self):
        p = OCRProvenance.from_dict({})
        assert p.engine == UNKNOWN_METADATA_VALUE

    def test_empty_string_engine_version_round_trips_as_empty_string(self):
        """L-17: ``to_dict`` must distinguish ``""`` (intentional empty) from
        ``None`` (unknown). Pre-fix the truthy guard
        ``if self.engine_version`` omitted ``""`` from the dict, and
        ``from_dict`` then defaulted the missing key back to ``None`` — so
        ``engine_version=""`` silently round-tripped to ``None``. Same for
        ``config_fingerprint``.
        """
        p = OCRProvenance(engine="x", engine_version="", config_fingerprint="")
        round_tripped = OCRProvenance.from_dict(p.to_dict())
        assert round_tripped.engine_version == ""
        assert round_tripped.config_fingerprint == ""


class TestOCRProvenanceImmutability:
    """L-15: ``models`` is a tuple so the ``frozen=True`` promise is real.

    A list field on a frozen dataclass blocked attribute reassignment but
    not in-place mutation — ``provenance.models.append(...)`` succeeded
    silently. Switching to ``tuple`` enforces actual immutability.
    """

    def test_models_is_tuple_not_list(self):
        p = OCRProvenance(engine="x", models=[OCRModelProvenance(name="m1")])
        assert isinstance(p.models, tuple)

    def test_models_default_is_tuple(self):
        p = OCRProvenance(engine="x")
        assert isinstance(p.models, tuple)
        assert p.models == ()

    def test_models_cannot_be_appended_to(self):
        p = OCRProvenance(engine="x")
        with pytest.raises(AttributeError):
            p.models.append(OCRModelProvenance(name="rogue"))  # type: ignore[attr-defined]

    def test_list_input_is_coerced_via_post_init(self):
        # Back-compat: callers passing a list still work; it's converted.
        p = OCRProvenance(
            engine="x",
            models=[OCRModelProvenance(name="m1"), OCRModelProvenance(name="m2")],
        )
        assert p.models == (
            OCRModelProvenance(name="m1"),
            OCRModelProvenance(name="m2"),
        )


class TestOCRProvenanceCoerce:
    def test_coerce_none(self):
        assert OCRProvenance.coerce(None) is None

    def test_coerce_provenance_returns_clone(self):
        p = OCRProvenance(engine="x")
        clone = OCRProvenance.coerce(p)
        assert clone is not None
        assert clone == p

    def test_coerce_provenance_short_circuits_to_same_instance(self):
        """L-16: ``coerce`` must short-circuit when given an ``OCRProvenance``.

        Pre-fix the function did ``OCRProvenance.from_dict(value.to_dict())``
        which produced a wasteful equal-but-not-identical copy. The class is
        frozen (L-15), so returning ``value`` directly is safe.
        """
        p = OCRProvenance(
            engine="tesseract",
            engine_version="5.3.0",
            models=(OCRModelProvenance(name="eng"),),
        )
        assert OCRProvenance.coerce(p) is p

    def test_coerce_dict(self):
        p = OCRProvenance.coerce({"engine": "x", "models": []})
        assert p is not None
        assert p.engine == "x"

    def test_coerce_invalid_raises(self):
        with pytest.raises(TypeError, match="OCRProvenance or dict"):
            OCRProvenance.coerce("not valid")
