"""
Data validation module for election CSV files.

This module validates CSV structure, checks for required columns,
and provides detailed warnings about missing or unexpected columns.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
import pandas as pd

from app.core.config import ELECTIONS_DIR
from app.core.settings import settings
from app.data.schema_notes import (
    REQUIRED_COLUMNS,
    OPTIONAL_COLUMNS,
    COLUMN_NORMALIZATION,
)

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of CSV validation."""
    
    def __init__(self):
        self.is_valid: bool = True
        self.missing_required: List[str] = []
        self.missing_optional: List[str] = []
        self.unexpected_columns: List[str] = []
        self.normalized_columns: Dict[str, str] = {}
        self.warnings: List[str] = []
        self.errors: List[str] = []
        self.row_count: int = 0
        self.column_count: int = 0
    
    def to_dict(self) -> Dict:
        """Convert validation result to dictionary."""
        return {
            "is_valid": self.is_valid,
            "missing_required": self.missing_required,
            "missing_optional": self.missing_optional,
            "unexpected_columns": self.unexpected_columns,
            "normalized_columns": self.normalized_columns,
            "warnings": self.warnings,
            "errors": self.errors,
            "row_count": self.row_count,
            "column_count": self.column_count,
        }


def normalize_column_name(col_name: str) -> str:
    """
    Normalize column name to standard format.
    
    Args:
        col_name: Original column name
        
    Returns:
        Normalized column name (lowercase, stripped, mapped)
    """
    # Convert to lowercase and strip whitespace
    normalized = col_name.lower().strip()
    
    # Check normalization mapping
    if normalized in COLUMN_NORMALIZATION:
        return COLUMN_NORMALIZATION[normalized]
    
    # Replace spaces with underscores
    normalized = normalized.replace(" ", "_")
    
    return normalized


def validate_csv_columns(
    df: pd.DataFrame,
    file_path: Optional[Path] = None,
    strict: Optional[bool] = None,
) -> ValidationResult:
    """
    Validate CSV columns against expected schema.
    
    Args:
        df: DataFrame to validate
        file_path: Optional path to CSV file (for logging)
        strict: Override settings.strict_validation if provided
        
    Returns:
        ValidationResult object with validation details
    """
    result = ValidationResult()
    strict_mode = strict if strict is not None else settings.strict_validation
    
    # Store basic info
    result.row_count = len(df)
    result.column_count = len(df.columns)
    
    # Normalize column names
    original_columns = df.columns.tolist()
    normalized_mapping = {}
    
    for orig_col in original_columns:
        norm_col = normalize_column_name(orig_col)
        normalized_mapping[orig_col] = norm_col
    
    result.normalized_columns = normalized_mapping
    
    # Get normalized column set
    normalized_columns_set = set(normalized_mapping.values())
    
    # Check required columns
    for req_col in REQUIRED_COLUMNS:
        if req_col not in normalized_columns_set:
            result.missing_required.append(req_col)
            result.is_valid = False
    
    # Check optional columns
    for opt_col in OPTIONAL_COLUMNS:
        if opt_col not in normalized_columns_set:
            result.missing_optional.append(opt_col)
    
    # Find unexpected columns
    all_expected = set(REQUIRED_COLUMNS + OPTIONAL_COLUMNS)
    unexpected = normalized_columns_set - all_expected
    result.unexpected_columns = sorted(list(unexpected))
    
    # Generate warnings and errors
    file_info = f" ({file_path})" if file_path else ""
    
    if result.missing_required:
        error_msg = (
            f"Missing required columns{file_info}: {', '.join(result.missing_required)}"
        )
        result.errors.append(error_msg)
        logger.error(error_msg)
        
        if strict_mode:
            result.is_valid = False
    
    if result.missing_optional and settings.log_warnings:
        warning_msg = (
            f"Missing optional columns{file_info}: {', '.join(result.missing_optional)}"
        )
        result.warnings.append(warning_msg)
        logger.warning(warning_msg)
    
    if result.unexpected_columns and settings.log_warnings:
        warning_msg = (
            f"Unexpected columns found{file_info}: {', '.join(result.unexpected_columns)}"
        )
        result.warnings.append(warning_msg)
        logger.info(warning_msg)
    
    # Check for empty DataFrame
    if result.row_count == 0:
        warning_msg = f"Empty CSV file{file_info}"
        result.warnings.append(warning_msg)
        logger.warning(warning_msg)
    
    return result


def apply_column_normalization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply column name normalization to DataFrame.
    
    Args:
        df: DataFrame with original column names
        
    Returns:
        DataFrame with normalized column names
    """
    normalized_mapping = {}
    for orig_col in df.columns:
        norm_col = normalize_column_name(orig_col)
        normalized_mapping[orig_col] = norm_col
    
    df_renamed = df.rename(columns=normalized_mapping)
    return df_renamed


def infer_election_year(df: pd.DataFrame, file_path: Optional[Path] = None) -> Optional[int]:
    """
    Attempt to infer election year from DataFrame or file path.
    
    Handles both Gregorian (AD) and Bikram Sambat (BS) year formats.
    Nepal uses Bikram Sambat calendar where years are approximately 57 years ahead.
    For example: BS 2079 = AD 2022, BS 2082 = AD 2025
    
    Args:
        df: DataFrame (may contain election_year column)
        file_path: Optional file path (may contain year in filename)
        
    Returns:
        Inferred election year (keeps BS year if detected from filename)
    """
    # Try from DataFrame column
    normalized_df = apply_column_normalization(df)
    if "election_year" in normalized_df.columns:
        year_values = normalized_df["election_year"].dropna().unique()
        if len(year_values) > 0:
            try:
                year = int(year_values[0])
                return year
            except (ValueError, TypeError):
                pass
    
    # Try from file path
    if file_path:
        filename = file_path.stem
        import re
        
        # Look for 4-digit year pattern (could be AD 19xx/20xx or BS 20xx)
        # BS years are typically 2070-2090 for recent elections
        year_match = re.search(r'\b(\d{4})\b', filename)
        if year_match:
            try:
                year = int(year_match.group())
                # Return the year as-is (could be BS or AD)
                # The caller can convert if needed
                return year
            except ValueError:
                pass
    
    return None
