from typing import Final, Optional

ALLOWED_TEXT_STYLE_LABELS: Final[frozenset[str]] = frozenset(
    {
        "regular",
        "all caps",
        "small caps",
        "italics",
        "bold",
        "blackletter",
        "underline",
        "strikethrough",
        "monospace",
        "handwritten",
    }
)

ALLOWED_COMPONENTS: Final[frozenset[str]] = frozenset(
    {
        "superscript",
        "subscript",
        "footnote marker",
        "drop cap",
    }
)

ALLOWED_TEXT_STYLE_LABEL_SCOPES: Final[frozenset[str]] = frozenset({"whole", "part"})


def _normalize_token(label: str) -> str:
    return " ".join(label.strip().lower().replace("_", " ").replace("-", " ").split())


def normalize_text_style_label(label: str) -> str:
    normalized = _normalize_token(label)

    if normalized not in ALLOWED_TEXT_STYLE_LABELS:
        compact = normalized.replace(" ", "")

        for allowed_label in ALLOWED_TEXT_STYLE_LABELS:
            if compact == allowed_label.replace(" ", ""):
                normalized = allowed_label
                break

    if normalized not in ALLOWED_TEXT_STYLE_LABELS:
        allowed = ", ".join(sorted(ALLOWED_TEXT_STYLE_LABELS))
        raise ValueError(
            f"Invalid text style label '{label}'. Allowed labels: {allowed}"
        )
    return normalized


def normalize_text_style_labels(labels: Optional[list[str]]) -> list[str]:
    if not labels:
        return ["regular"]
    normalized = [normalize_text_style_label(label) for label in labels]
    return list(dict.fromkeys(normalized))


def normalize_text_style_label_scope(scope: Optional[str]) -> str:
    if scope is None:
        return "whole"

    normalized = _normalize_token(scope)

    if normalized not in ALLOWED_TEXT_STYLE_LABEL_SCOPES:
        allowed = ", ".join(sorted(ALLOWED_TEXT_STYLE_LABEL_SCOPES))
        raise ValueError(
            f"Invalid text style label scope '{scope}'. Allowed scopes: {allowed}"
        )
    return normalized


def normalize_text_style_label_scopes(
    labels: list[str], scopes: Optional[dict[str, str]]
) -> dict[str, str]:
    normalized_labels = [normalize_text_style_label(label) for label in labels]
    if not normalized_labels:
        normalized_labels = ["regular"]
    normalized_labels = list(dict.fromkeys(normalized_labels))
    normalized_scopes = {label: "whole" for label in normalized_labels}

    if not scopes:
        return normalized_scopes

    for label, scope in scopes.items():
        normalized_label = normalize_text_style_label(label)
        if normalized_label not in normalized_scopes:
            allowed_labels = ", ".join(sorted(normalized_scopes.keys()))
            raise ValueError(
                f"Unknown style label '{label}' in text_style_label_scopes. "
                f"Must match text_style_labels: {allowed_labels}"
            )
        normalized_scopes[normalized_label] = normalize_text_style_label_scope(scope)

    return normalized_scopes


def normalize_word_component(component: str) -> str:
    return _normalize_component(
        component,
        allowed_components=ALLOWED_COMPONENTS,
        label_type="word component",
    )


def normalize_word_components(components: Optional[list[str]]) -> list[str]:
    if not components:
        return []
    normalized = [normalize_word_component(component) for component in components]
    return list(dict.fromkeys(normalized))


def normalize_character_component(component: str) -> str:
    return _normalize_component(
        component,
        allowed_components=ALLOWED_COMPONENTS,
        label_type="character component",
    )


def _normalize_component(
    component: str,
    *,
    allowed_components: frozenset[str],
    label_type: str,
) -> str:
    normalized = _normalize_token(component)

    if normalized not in allowed_components:
        compact = normalized.replace(" ", "")

        for allowed_component in allowed_components:
            if compact == allowed_component.replace(" ", ""):
                normalized = allowed_component
                break

    if normalized not in allowed_components:
        allowed = ", ".join(sorted(allowed_components))
        raise ValueError(
            f"Invalid {label_type} '{component}'. Allowed components: {allowed}"
        )
    return normalized


def normalize_character_components(components: Optional[list[str]]) -> list[str]:
    if not components:
        return []
    normalized = [normalize_character_component(component) for component in components]
    return list(dict.fromkeys(normalized))
