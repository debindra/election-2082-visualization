"""
Analytics module for party retrenchment vs expansion.
"""
from typing import Dict, Optional
import pandas as pd

from app.utils.metrics import compute_party_footprint


def analyze_party_retrenchment(
    current_df: pd.DataFrame,
    previous_df: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Analyze party retrenchment vs expansion (Party Footprint Index).
    
    Args:
        current_df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with party retrenchment analysis
    """
    metrics = compute_party_footprint(current_df, previous_df)
    
    # Add party-level details
    party_details = {}
    if "party" in current_df.columns and "constituency" in current_df.columns:
        for party in current_df["party"].unique():
            party_df = current_df[current_df["party"] == party]
            party_details[party] = {
                "candidate_count": len(party_df),
                "constituency_count": party_df["constituency"].nunique() if "constituency" in party_df.columns else 0,
                "candidate_ids": party_df["candidate_id"].astype(str).tolist() if "candidate_id" in party_df.columns else [],
            }
    
    return {
        "metrics": metrics,
        "party_details": party_details,
    }
