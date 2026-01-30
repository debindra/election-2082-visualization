"""
Analytics module for education profile evolution.
"""
from typing import Dict, Optional
import pandas as pd

from app.utils.metrics import compute_education_evolution


def analyze_education_evolution(
    current_df: pd.DataFrame,
    previous_df: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Analyze education profile evolution.
    
    Args:
        current_df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with education evolution analysis
    """
    metrics = compute_education_evolution(current_df, previous_df)
    
    return {
        "metrics": metrics,
    }
