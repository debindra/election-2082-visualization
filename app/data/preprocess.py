"""
Data preprocessing module for election data.

Handles data cleaning, type conversion, and enrichment.
"""
import logging
import re
from typing import Dict, Optional
from datetime import datetime
import pandas as pd
import numpy as np

from app.data.validator import apply_column_normalization, infer_election_year
from app.data.schema_notes import DISTRICT_TO_PROVINCE

logger = logging.getLogger(__name__)


def clean_boolean_column(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """
    Clean and convert boolean column.
    
    Handles various boolean representations:
    - True/False
    - 1/0
    - Yes/No
    - Y/N
    - T/F
    
    Args:
        df: DataFrame
        col_name: Column name to clean
        
    Returns:
        DataFrame with cleaned boolean column
    """
    if col_name not in df.columns:
        return df
    
    df = df.copy()
    
    def convert_to_bool(value):
        if pd.isna(value):
            return False
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return bool(value)
        value_str = str(value).lower().strip()
        if value_str in ['true', 'yes', 'y', 't', '1']:
            return True
        if value_str in ['false', 'no', 'n', 'f', '0']:
            return False
        return False
    
    df[col_name] = df[col_name].apply(convert_to_bool)
    return df


# Mapping for gender normalization: Nepali, English, and common variants -> M/F/Other
GENDER_NORMALIZATION = {
    # Male
    "पुरुष": "M", "male": "M", "m": "M", "म": "M",
    # Female
    "महिला": "F", "female": "F", "f": "F", "फ": "F",
    # Other / third gender (keep as Other for inclusivity)
    "अन्य": "Other", "other": "Other", "तीस्रो लिङ्ग": "Other", "third gender": "Other",
}


def normalize_gender_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize gender column to M/F/Other for consistent filtering and analytics.
    Handles Nepali (पुरुष/महिला), English, and common variants.
    """
    if "gender" not in df.columns:
        return df
    df = df.copy()

    def _normalize(val):
        if pd.isna(val):
            return np.nan
        s = str(val).strip().lower()
        if not s or s in ("nan", "none"):
            return np.nan
        # Check Nepali first (case-sensitive for Devanagari)
        orig = str(val).strip()
        if orig in GENDER_NORMALIZATION:
            return GENDER_NORMALIZATION[orig]
        if s in GENDER_NORMALIZATION:
            return GENDER_NORMALIZATION[s]
        # Partial match for common patterns
        if "पुरुष" in orig or "male" in s or s == "m":
            return "M"
        if "महिला" in orig or "female" in s or s == "f":
            return "F"
        if "अन्य" in orig or "other" in s or "तीस्रो" in orig or "third" in s:
            return "Other"
        return orig  # Keep unrecognized as-is

    df["gender"] = df["gender"].apply(_normalize)
    logger.info(f"Normalized gender: {df['gender'].dropna().value_counts().to_dict()}")
    return df


def clean_numeric_column(df: pd.DataFrame, col_name: str) -> pd.DataFrame:
    """
    Clean and convert numeric column.
    
    Args:
        df: DataFrame
        col_name: Column name to clean
        
    Returns:
        DataFrame with cleaned numeric column
    """
    if col_name not in df.columns:
        return df
    
    df = df.copy()
    
    # Convert to numeric, coercing errors to NaN
    df[col_name] = pd.to_numeric(df[col_name], errors='coerce')
    
    return df


def preprocess_election_data(
    df: pd.DataFrame,
    file_path: Optional[str] = None,
    election_year: Optional[int] = None,
) -> pd.DataFrame:
    """
    Preprocess election DataFrame.
    
    Steps:
    1. Normalize column names
    2. Infer election year if not provided
    3. Clean data types
    4. Add computed columns if needed
    
    Args:
        df: Raw DataFrame from CSV
        file_path: Optional file path for year inference
        election_year: Optional explicit election year
        
    Returns:
        Preprocessed DataFrame
    """
    from pathlib import Path
    
    # Step 1: Normalize column names
    df = apply_column_normalization(df)
    
    # Step 2: Infer election year
    if election_year is None:
        path_obj = Path(file_path) if file_path else None
        inferred_year = infer_election_year(df, path_obj)
        if inferred_year:
            election_year = inferred_year
    
    # Add election_year column if missing
    if "election_year" not in df.columns:
        if election_year:
            df["election_year"] = election_year
            logger.info(f"Added election_year column with value {election_year}")
        else:
            logger.warning("Could not infer election_year. Some analyses may fail.")
    
    # Step 3: Clean boolean columns
    boolean_columns = ["is_independent", "is_winner"]
    for col in boolean_columns:
        if col in df.columns:
            df = clean_boolean_column(df, col)
    
    # Step 4: Clean numeric columns
    numeric_columns = [
        "age",
        "votes_received",
        "votes_percentage",
        "margin",
        "total_voters",
        "voter_turnout",
    ]
    for col in numeric_columns:
        if col in df.columns:
            df = clean_numeric_column(df, col)
    
    # Step 5: Clean text columns (strip whitespace)
    text_columns = [
        "candidate_name",
        "party",
        "district",
        "constituency",
        "province",
        "gender",
        "education_level",
        "academic_qualification_generalized",
        "birth_district",
        "symbol",
        "candidate_name_en",
        "district_en",
        "birth_place_en",
        "party_en",
        "province_en",
        "province_np",
    ]
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # Replace 'nan' strings with actual NaN
            df[col] = df[col].replace('nan', np.nan)
            df[col] = df[col].replace('', np.nan)
    
    # Step 5b: Normalize gender to M/F/Other (Nepali, English, and common variants)
    if "gender" in df.columns:
        df = normalize_gender_column(df)
    
    # Step 6: Ensure candidate_id is string (preserve leading zeros)
    if "candidate_id" in df.columns:
        df["candidate_id"] = df["candidate_id"].astype(str)
    
    # Step 7: Ensure election_year is integer
    if "election_year" in df.columns:
        df["election_year"] = pd.to_numeric(df["election_year"], errors='coerce').astype('Int64')
    
    # Step 8: Infer province from district if province is missing
    if "province" not in df.columns or df["province"].isna().all():
        df = infer_province_from_district(df)
    
    # Step 9: Calculate age from DOB if age is missing
    if "age" not in df.columns or df["age"].isna().all():
        df = calculate_age_from_dob(df, election_year)
    
    # Step 10: Create election_area (display name) combining district + constituency
    # This matches the format used by election.onlinekhabar.com (e.g., "इलाम - २", "चितवन - १")
    df = create_election_area_display_name(df)
    
    # Step 11: Add enriched columns (is_independent from party, is_winner, etc.)
    df = enrich_data(df)
    
    return df


def infer_province_from_district(df: pd.DataFrame) -> pd.DataFrame:
    """
    Infer province from district using the district-to-province mapping.
    
    Args:
        df: DataFrame with district column
        
    Returns:
        DataFrame with province column added
    """
    if "district" not in df.columns:
        return df
    
    df = df.copy()
    
    def get_province(district):
        if pd.isna(district):
            return None
        district_lower = str(district).lower().strip()
        # Try direct match
        if district_lower in DISTRICT_TO_PROVINCE:
            return DISTRICT_TO_PROVINCE[district_lower]
        # Try partial match
        for key, province in DISTRICT_TO_PROVINCE.items():
            if key in district_lower or district_lower in key:
                return province
        return None
    
    df["province"] = df["district"].apply(get_province)
    logger.info(f"Inferred province for {df['province'].notna().sum()} of {len(df)} rows")
    return df


def calculate_age_from_dob(df: pd.DataFrame, election_year: Optional[int] = None) -> pd.DataFrame:
    """
    Calculate age from date of birth.
    
    Handles both Gregorian (AD) and Bikram Sambat (BS) date formats.
    BS years (e.g., 2044) are approximately 57 years ahead of AD.
    
    Args:
        df: DataFrame with dob column
        election_year: Election year for age calculation reference
        
    Returns:
        DataFrame with age column added
    """
    if "dob" not in df.columns:
        return df
    
    df = df.copy()
    
    # Determine reference year for age calculation
    ref_year = election_year
    if ref_year is None:
        if "election_year" in df.columns and df["election_year"].notna().any():
            ref_year = int(df["election_year"].dropna().iloc[0])
        else:
            ref_year = datetime.now().year
    
    # If reference year is in BS (> 2000 and < 2100, likely BS year like 2079, 2082)
    # Convert to AD for age calculation
    if ref_year > 2050:  # BS year
        ref_year_ad = ref_year - 57
    else:
        ref_year_ad = ref_year
    
    def extract_birth_year(dob):
        if pd.isna(dob):
            return None
        dob_str = str(dob).strip()
        
        # Try to extract year from various formats
        # Format: YYYY-MM-DD or YYYY/MM/DD
        year_match = re.match(r'^(\d{4})[-/]', dob_str)
        if year_match:
            year = int(year_match.group(1))
            # If year is in BS (> 2000), convert to AD
            if year > 2000:
                year = year - 57
            return year
        
        # Format: DD-MM-YYYY or DD/MM/YYYY
        year_match = re.search(r'[-/](\d{4})$', dob_str)
        if year_match:
            year = int(year_match.group(1))
            if year > 2000:
                year = year - 57
            return year
        
        return None
    
    birth_years = df["dob"].apply(extract_birth_year)
    df["age"] = ref_year_ad - birth_years
    
    # Clean up invalid ages
    df.loc[df["age"] < 18, "age"] = np.nan
    df.loc[df["age"] > 120, "age"] = np.nan
    
    valid_ages = df["age"].notna().sum()
    logger.info(f"Calculated age for {valid_ages} of {len(df)} rows")
    
    return df


def create_election_area_display_name(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a user-friendly election area display name.
    
    Combines district name with constituency number to create names like:
    - "इलाम - १" (Ilam - 1)
    - "चितवन - २" (Chitwan - 2)
    
    This matches the format used by election.onlinekhabar.com
    
    Args:
        df: DataFrame with district and constituency columns
        
    Returns:
        DataFrame with election_area_display column added
    """
    if "constituency" not in df.columns or "district" not in df.columns:
        return df
    
    df = df.copy()
    
    def extract_constituency_number(const_name):
        """Extract the number from constituency name like 'प्रतिनिधि सभा निर्वाचन क्षेत्र 1'"""
        if pd.isna(const_name):
            return ""
        
        const_str = str(const_name)
        
        # Map Arabic numerals to Nepali numerals
        arabic_to_nepali = {
            '0': '०', '1': '१', '2': '२', '3': '३', '4': '४',
            '5': '५', '6': '६', '7': '७', '8': '८', '9': '९'
        }
        
        # Try to extract number at the end of the string
        import re
        numbers = re.findall(r'\d+', const_str)
        if numbers:
            number = numbers[-1]  # Get the last number
            # Convert to Nepali numerals
            nepali_number = ''.join(arabic_to_nepali.get(d, d) for d in number)
            return nepali_number
        
        return ""
    
    def create_display_name(row):
        district = row.get("district", "")
        const_num = extract_constituency_number(row.get("constituency", ""))
        
        if pd.notna(district) and const_num:
            return f"{district} - {const_num}"
        elif pd.notna(district):
            return str(district)
        else:
            return str(row.get("constituency", ""))
    
    df["election_area_display"] = df.apply(create_display_name, axis=1)
    
    logger.info(f"Created election_area_display for {df['election_area_display'].notna().sum()} rows")
    
    return df


def enrich_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add computed/enriched columns to DataFrame.
    
    Args:
        df: Preprocessed DataFrame
        
    Returns:
        DataFrame with enriched columns
    """
    df = df.copy()
    
    # Add is_independent flag if party column suggests it
    # IMPORTANT: Treat only true independents (no party) as "स्वतन्त्र"/"स्वतंत्र" or exactly "independent"
    if "is_independent" not in df.columns and "party" in df.columns:
        party_str = df["party"].astype(str).str.strip()
        party_lower = party_str.str.lower()

        # Exact match for Nepali independents (exclude e.g. "राष्ट्रिय स्वतन्त्र पार्टी")
        nepali_independent = party_str.isin(["स्वतन्त्र", "स्वतंत्र"])

        # Exact / near-exact English independent labels
        english_independent = party_lower.isin(
            [
                "independent",
                "independent candidate",
                "independent (no party)",
            ]
        )

        df["is_independent"] = nepali_independent | english_independent
    
    # Add winner flag if votes_received and votes_percentage suggest it
    # (This is a heuristic - actual winner determination should come from data)
    if "is_winner" not in df.columns:
        if "votes_received" in df.columns:
            # Mark highest vote getter per constituency as winner
            if "constituency" in df.columns:
                df["is_winner"] = (
                    df.groupby(["election_year", "constituency"])["votes_received"]
                    .transform(lambda x: x == x.max())
                )
    
    return df
