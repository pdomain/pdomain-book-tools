from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

UNKNOWN_METADATA_VALUE = "unknown"


@dataclass(frozen=True)
class OCRModelProvenance:
    name: str
    version: str | None = None
    weights_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {"name": self.name}
        if self.version:
            result["version"] = self.version
        if self.weights_id:
            result["weights_id"] = self.weights_id
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OCRModelProvenance":
        return cls(
            name=str(data.get("name", UNKNOWN_METADATA_VALUE)),
            version=(str(data["version"]) if data.get("version") is not None else None),
            weights_id=(
                str(data["weights_id"]) if data.get("weights_id") is not None else None
            ),
        )


@dataclass(frozen=True)
class OCRProvenance:
    engine: str = UNKNOWN_METADATA_VALUE
    engine_version: str | None = None
    # Stored as a tuple so the frozen=True immutability promise is real:
    # ``provenance.models.append(...)`` would have succeeded silently on a
    # list, defeating the dataclass's frozen contract. ``__post_init__``
    # coerces any incoming list/iterable to a tuple. (L-15)
    models: tuple[OCRModelProvenance, ...] = field(default_factory=tuple)
    config_fingerprint: str | None = None

    def __post_init__(self) -> None:
        # Tolerate callers (and legacy code) constructing with a list.
        # ``object.__setattr__`` is required because the dataclass is frozen.
        if not isinstance(self.models, tuple):
            object.__setattr__(self, "models", tuple(self.models))

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "engine": self.engine,
            "models": [model.to_dict() for model in self.models],
        }
        # L-17: serialize ``None`` and explicit ``""`` distinctly. The
        # truthy guard ``if self.engine_version`` previously omitted ``""``
        # from the dict, and ``from_dict``'s ``is not None`` check then
        # defaulted the missing key back to ``None`` — silently flipping
        # an explicit empty value to "unknown" on every round-trip.
        if self.engine_version is not None:
            result["engine_version"] = self.engine_version
        if self.config_fingerprint is not None:
            result["config_fingerprint"] = self.config_fingerprint
        return result

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "OCRProvenance":
        raw_models = data.get("models", [])
        models: list[OCRModelProvenance] = []
        if isinstance(raw_models, list):
            for model in raw_models:
                if isinstance(model, str) and model:
                    models.append(OCRModelProvenance(name=model))
                elif isinstance(model, dict):
                    name = model.get("name") or model.get("model")
                    if not isinstance(name, str) or not name:
                        continue
                    models.append(
                        OCRModelProvenance(
                            name=name,
                            version=(
                                str(model["version"])
                                if model.get("version") is not None
                                else None
                            ),
                            weights_id=(
                                str(model["weights_id"])
                                if model.get("weights_id") is not None
                                else None
                            ),
                        )
                    )

        return cls(
            engine=str(data.get("engine", UNKNOWN_METADATA_VALUE)),
            engine_version=(
                str(data["engine_version"])
                if data.get("engine_version") is not None
                else None
            ),
            models=models,
            config_fingerprint=(
                str(data["config_fingerprint"])
                if data.get("config_fingerprint") is not None
                else None
            ),
        )

    @classmethod
    def coerce(
        cls, value: "OCRProvenance | dict[str, Any] | None"
    ) -> "OCRProvenance | None":
        if value is None:
            return None
        if isinstance(value, OCRProvenance):
            # L-16: the class is frozen (L-15 made ``models`` a tuple), so
            # returning the input directly is safe and avoids a wasteful
            # ``from_dict(value.to_dict())`` round-trip.
            return value
        if isinstance(value, dict):
            return OCRProvenance.from_dict(value)
        raise TypeError("ocr_provenance must be an OCRProvenance or dict")
