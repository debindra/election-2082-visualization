"""
Analytics module for candidate density vs voter choice.
"""
from typing import Dict
import pandas as pd

from app.utils.metrics import compute_candidate_density


def analyze_candidate_density(current_df: pd.DataFrame) -> Dict:
    """
    Analyze candidate density vs voter choice.
    
    Args:
        current_df: Current election DataFrame
        
    Returns:
        Dictionary with candidate density analysis
    """
    metrics = compute_candidate_density(current_df)
    
    # Breakdown by constituency
    if "constituency" in current_df.columns:
        constituency_breakdown = {}
        for constituency in current_df["constituency"].unique():
            constituency_df = current_df[current_df["constituency"] == constituency]
            constituency_breakdown[constituency] = {
                "candidate_count": len(constituency_df),
                "candidate_ids": constituency_df["candidate_id"].astype(str).tolist() if "candidate_id" in constituency_df.columns else [],
            }
        metrics["by_constituency"] = constituency_breakdown
    
    return {
        "metrics": metrics,
    }
