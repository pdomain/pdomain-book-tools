from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any, Literal


class Converter(StrEnum):
    """Grayscale conversion algorithm."""

    luma = "luma"
    luma_bt709 = "luma_bt709"
    lab_l = "lab_l"
    color2gray = "color2gray"
    best_channel = "best_channel"


@dataclass(frozen=True)
class FlattenConfig:
    """Parameters for background-flattening pre-pass."""

    enabled: bool = False
    radius: int = 64
    strength: float = 1.0


@dataclass(frozen=True)
class ClaheConfig:
    """Parameters for CLAHE contrast-enhancement post-pass."""

    enabled: bool = False
    clip_limit: float = 2.0
    tile_grid: int = 8


@dataclass(frozen=True)
class Color2GrayParams:
    """Tuning parameters for the color2gray perceptual converter."""

    radius: int = 300
    samples: int = 4
    iterations: int = 10
    enhance_shadows: bool = False


@dataclass(frozen=True)
class GrayscaleConfig:
    """Full grayscale-pipeline configuration: flatten → converter → CLAHE."""

    flatten: FlattenConfig = field(default_factory=FlattenConfig)
    converter: Converter = Converter.luma
    channel: Literal["green", "red", "blue", "auto"] = "green"
    color2gray: Color2GrayParams = field(default_factory=Color2GrayParams)
    clahe: ClaheConfig = field(default_factory=ClaheConfig)
    output_range: tuple[int, int] | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialise to a plain dict suitable for JSON round-tripping."""
        d = asdict(self)
        d["converter"] = self.converter.value
        d["output_range"] = list(self.output_range) if self.output_range else None
        return d

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> GrayscaleConfig:
        """Deserialise from the dict produced by :meth:`to_dict`."""
        try:
            conv = Converter(d.get("converter", "luma"))
        except ValueError as exc:
            raise ValueError(f"unknown converter: {d.get('converter')!r}") from exc
        rng = d.get("output_range")
        return cls(
            flatten=FlattenConfig(**(d.get("flatten") or {})),
            converter=conv,
            channel=d.get("channel", "green"),
            color2gray=Color2GrayParams(**(d.get("color2gray") or {})),
            clahe=ClaheConfig(**(d.get("clahe") or {})),
            output_range=(int(rng[0]), int(rng[1])) if rng else None,
        )
