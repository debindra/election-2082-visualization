"""
Utility Functions for RAG QA System
"""
import re
from datetime import datetime
from typing import Optional


def calculate_age_from_dob(dob_str: str, reference_year: int = 2082) -> Optional[int]:
    """
    Calculate age from DOB string for a reference year.
    
    Args:
        dob_str: DOB in format YYYY-MM-DD or similar
        reference_year: Reference year (e.g., 2082)
        
    Returns:
        Age as integer, or None if DOB invalid
    """
    if not dob_str or dob_str.lower() in ['null', 'n/a', 'none', '-']:
        return None
    
    # Try to extract year from DOB
    year_match = re.search(r'(\d{4})', dob_str)
    if not year_match:
        return None
    
    try:
        birth_year = int(year_match.group(1))
        age = reference_year - birth_year
        return max(0, age)  # Ensure age is non-negative
    except (ValueError, AttributeError):
        return None


def detect_query_language(query: str) -> str:
    """
    Detect if query is in Nepali or English.
    
    Args:
        query: User's query string
        
    Returns:
        'nepali' if Nepali characters detected, 'english' otherwise
    """
    nepali_chars = set('ँंःअआइईउऊएऐऑओकगखघङचछजटडणढनपफबमयरलवशसहषहाािीीुूृेोौाौृृेैाौॉोांाःंौः')
    
    # Check if query contains significant Nepali characters
    if any(char in nepali_chars for char in query):
        return "nepali"
    else:
        return "english"


def format_age_for_display(age: Optional[int], dob: str) -> str:
    """
    Format age for display in traditional election format.
    
    Args:
        age: Calculated age (can be None)
        dob: Original DOB string
        
    Returns:
        Formatted age string for display
    """
    if age is not None:
        return "उमेर उपलब्ध छैन" if detect_query_language(dob) == "nepali" else "Age not available"
    else:
        return str(age)


def format_education_for_display(education: Optional[str]) -> str:
    """
    Format education for display in traditional election format.
    
    Args:
        education: Education qualification string
        
    Returns:
        Formatted education string
    """
    if not education or education.lower() in ['null', 'n/a', 'none', '-', '']:
        return "शैक्षिक योग्यात उपलब्ध छैन" if detect_query_language(education) == "nepali" else "Education not available"
    return education
