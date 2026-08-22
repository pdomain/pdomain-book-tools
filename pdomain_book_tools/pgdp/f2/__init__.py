"""Lossless parsing primitives for PGDP F2 artifacts."""

from __future__ import annotations

from pdomain_book_tools.pgdp.f2.offsets import (
    DecodedF2Character,
    LexicalF2Document,
    LexicalF2Index,
    LexicalF2Page,
    LexicalF2PageIndex,
    read_lexical_f2_index,
    read_lexical_f2_json,
    read_lexical_f2_page,
)
from pdomain_book_tools.pgdp.f2.parser import F2Parser
from pdomain_book_tools.pgdp.f2.project_rules import ProjectRule, ProjectRuleRegistry
from pdomain_book_tools.pgdp.f2.tokens import (
    F2JsonDocument,
    F2JsonPage,
    F2NormalizationKind,
    F2NormalizationOperation,
    F2PageTokens,
    F2Token,
    F2TokenKind,
    F2Warning,
    read_f2_json,
    read_f2_json_page,
    tokenize_f2,
)

__all__ = [
    "DecodedF2Character",
    "F2JsonDocument",
    "F2JsonPage",
    "F2NormalizationKind",
    "F2NormalizationOperation",
    "F2PageTokens",
    "F2Parser",
    "F2Token",
    "F2TokenKind",
    "F2Warning",
    "LexicalF2Document",
    "LexicalF2Index",
    "LexicalF2Page",
    "LexicalF2PageIndex",
    "ProjectRule",
    "ProjectRuleRegistry",
    "read_f2_json",
    "read_f2_json_page",
    "read_lexical_f2_index",
    "read_lexical_f2_json",
    "read_lexical_f2_page",
    "tokenize_f2",
]
