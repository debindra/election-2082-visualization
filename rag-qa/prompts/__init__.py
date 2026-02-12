"""
Prompts Module

Contains all prompt templates.
"""
from .system_prompt import (
    SYSTEM_PROMPT,
    QUERY_CLASSIFICATION_PROMPT,
    build_context_prompt,
    build_exact_lookup_prompt,
    build_analytical_prompt,
    build_comparison_prompt,
    build_aggregation_prompt,
    build_complex_prompt
)

__all__ = [
    "SYSTEM_PROMPT",
    "QUERY_CLASSIFICATION_PROMPT",
    "build_context_prompt",
    "build_exact_lookup_prompt",
    "build_analytical_prompt",
    "build_comparison_prompt",
    "build_aggregation_prompt",
    "build_complex_prompt"
]
