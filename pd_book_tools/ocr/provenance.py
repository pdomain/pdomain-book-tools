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
    models: list[OCRModelProvenance] = field(default_factory=list)
    config_fingerprint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "engine": self.engine,
            "models": [model.to_dict() for model in self.models],
        }
        if self.engine_version:
            result["engine_version"] = self.engine_version
        if self.config_fingerprint:
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
            return OCRProvenance.from_dict(value.to_dict())
        if isinstance(value, dict):
            return OCRProvenance.from_dict(value)
        raise TypeError("ocr_provenance must be an OCRProvenance or dict")
