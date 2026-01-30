"""
Analytics module for independent candidate structural shift.
"""
from typing import Dict, Optional
import pandas as pd

from app.utils.metrics import compute_independent_shift


def analyze_independent_shift(
    current_df: pd.DataFrame,
    previous_df: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Analyze independent candidate structural shift across elections.
    
    Args:
        current_df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with independent shift analysis
    """
    metrics = compute_independent_shift(current_df, previous_df)
    
    # Add detailed breakdown by geography
    breakdown = {}
    if "province" in current_df.columns:
        province_breakdown = {}
        for province in current_df["province"].unique():
            province_df = current_df[current_df["province"] == province]
            province_metrics = compute_independent_shift(province_df)
            province_breakdown[province] = province_metrics
        breakdown["by_province"] = province_breakdown
    
    if "district" in current_df.columns:
        district_breakdown = {}
        for district in current_df["district"].unique():
            district_df = current_df[current_df["district"] == district]
            district_metrics = compute_independent_shift(district_df)
            district_breakdown[district] = district_metrics
        breakdown["by_district"] = district_breakdown
    
    return {
        "metrics": metrics,
        "breakdown": breakdown,
    }
