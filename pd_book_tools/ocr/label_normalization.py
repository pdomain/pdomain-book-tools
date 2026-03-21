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

TEXT_STYLE_LABEL_ALIASES: Final[dict[str, str]] = {
    "italic": "italics",
    "ital": "italics",
    "monospaced": "monospace",
    "typewriter": "monospace",
}

ALLOWED_WORD_COMPONENTS: Final[frozenset[str]] = frozenset(
    {
        "has superscript",
        "has subscript",
        "has starting footnote marker",
        "has ending footnote marker",
        "has drop cap",
    }
)

WORD_COMPONENT_ALIASES: Final[dict[str, str]] = {
    "superscript": "has superscript",
    "subscript": "has subscript",
    "start footnote marker": "has starting footnote marker",
    "start footnote": "has starting footnote marker",
    "footnote start marker": "has starting footnote marker",
    "starting footnote marker": "has starting footnote marker",
    "has start footnote marker": "has starting footnote marker",
    "end footnote marker": "has ending footnote marker",
    "end footnote": "has ending footnote marker",
    "footnote end marker": "has ending footnote marker",
    "ending footnote marker": "has ending footnote marker",
    "has end footnote marker": "has ending footnote marker",
    "drop cap": "has drop cap",
    "has dropcap": "has drop cap",
}

ALLOWED_TEXT_STYLE_LABEL_SCOPES: Final[frozenset[str]] = frozenset({"whole", "part"})

TEXT_STYLE_LABEL_SCOPE_ALIASES: Final[dict[str, str]] = {
    "entire": "whole",
    "full": "whole",
    "word": "whole",
    "partial": "part",
    "portion": "part",
}


def _normalize_token(label: str) -> str:
    return " ".join(label.strip().lower().replace("_", " ").replace("-", " ").split())


def normalize_text_style_label(label: str) -> str:
    normalized = _normalize_token(label)
    normalized = TEXT_STYLE_LABEL_ALIASES.get(normalized, normalized)

    if normalized not in ALLOWED_TEXT_STYLE_LABELS:
        compact = normalized.replace(" ", "")

        for allowed_label in ALLOWED_TEXT_STYLE_LABELS:
            if compact == allowed_label.replace(" ", ""):
                normalized = allowed_label
                break

        if normalized not in ALLOWED_TEXT_STYLE_LABELS:
            for alias, canonical in TEXT_STYLE_LABEL_ALIASES.items():
                if compact == alias.replace(" ", ""):
                    normalized = canonical
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
    normalized = TEXT_STYLE_LABEL_SCOPE_ALIASES.get(normalized, normalized)

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
    normalized = _normalize_token(component)
    normalized = WORD_COMPONENT_ALIASES.get(normalized, normalized)

    if normalized not in ALLOWED_WORD_COMPONENTS:
        compact = normalized.replace(" ", "")

        for allowed_component in ALLOWED_WORD_COMPONENTS:
            if compact == allowed_component.replace(" ", ""):
                normalized = allowed_component
                break

        if normalized not in ALLOWED_WORD_COMPONENTS:
            for alias, canonical in WORD_COMPONENT_ALIASES.items():
                if compact == alias.replace(" ", ""):
                    normalized = canonical
                    break

    if normalized not in ALLOWED_WORD_COMPONENTS:
        allowed = ", ".join(sorted(ALLOWED_WORD_COMPONENTS))
        raise ValueError(
            f"Invalid word component '{component}'. Allowed components: {allowed}"
        )
    return normalized


def normalize_word_components(components: Optional[list[str]]) -> list[str]:
    if not components:
        return []
    normalized = [normalize_word_component(component) for component in components]
    return list(dict.fromkeys(normalized))
