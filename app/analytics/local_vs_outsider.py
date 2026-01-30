"""
Analytics module for local vs outsider candidate trend.
"""
from typing import Dict
import pandas as pd

from app.utils.metrics import compute_local_vs_outsider


def analyze_local_vs_outsider(current_df: pd.DataFrame) -> Dict:
    """
    Analyze local vs outsider candidate trend.
    
    Args:
        current_df: Current election DataFrame
        
    Returns:
        Dictionary with local/outsider analysis
    """
    metrics = compute_local_vs_outsider(current_df)
    
    # Breakdown by province
    province_breakdown = {}
    if "province" in current_df.columns:
        for province in current_df["province"].unique():
            province_df = current_df[current_df["province"] == province]
            province_metrics = compute_local_vs_outsider(province_df)
            province_breakdown[province] = province_metrics
    
    return {
        "metrics": metrics,
        "breakdown": {
            "by_province": province_breakdown,
        },
    }
