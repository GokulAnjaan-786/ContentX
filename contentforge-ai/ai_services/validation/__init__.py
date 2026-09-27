"""Validation and verification module for ContentForge AI."""
from ai_services.validation.schema_validator import (
    validate_output_schema,
    get_schema_for_type,
    OUTPUT_SCHEMA_MAP,
)
from ai_services.validation.fact_checker import (
    verify_output_facts,
    check_cross_output_consistency,
)

__all__ = [
    "validate_output_schema",
    "get_schema_for_type",
    "OUTPUT_SCHEMA_MAP",
    "verify_output_facts",
    "check_cross_output_consistency",
]
