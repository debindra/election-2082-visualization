"""
Analytics module for candidate age trends (leadership renewal).
"""
from typing import Dict, Optional
import pandas as pd

from app.utils.metrics import compute_age_trends


def analyze_age_trends(
    current_df: pd.DataFrame,
    previous_df: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Analyze candidate age trends (leadership renewal).
    
    Args:
        current_df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with age trend analysis
    """
    metrics = compute_age_trends(current_df, previous_df)
    
    # Add age distribution
    if "age" in current_df.columns:
        ages = current_df["age"].dropna()
        if len(ages) > 0:
            metrics["age_distribution"] = {
                "min": int(ages.min()),
                "max": int(ages.max()),
                "q25": round(ages.quantile(0.25), 1),
                "q50": round(ages.median(), 1),
                "q75": round(ages.quantile(0.75), 1),
            }
    
    # Breakdown by party
    party_age_breakdown = {}
    if "party" in current_df.columns and "age" in current_df.columns:
        for party in current_df["party"].unique():
            party_df = current_df[current_df["party"] == party]
            party_ages = party_df["age"].dropna()
            if len(party_ages) > 0:
                party_age_breakdown[party] = {
                    "average_age": round(party_ages.mean(), 1),
                    "median_age": round(party_ages.median(), 1),
                }
    
    return {
        "metrics": metrics,
        "party_age_breakdown": party_age_breakdown,
    }
