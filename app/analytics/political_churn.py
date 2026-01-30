"""
Analytics module for political churn index.
"""
from typing import Dict, Optional
import pandas as pd

from app.utils.metrics import compute_political_churn


def analyze_political_churn(
    current_df: pd.DataFrame,
    previous_df: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Analyze political churn index (candidate turnover).
    
    Args:
        current_df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with political churn analysis
    """
    metrics = compute_political_churn(current_df, previous_df)
    
    # Add candidate-level details if both elections available
    if previous_df is not None and "candidate_id" in current_df.columns and "candidate_id" in previous_df.columns:
        current_ids = set(current_df["candidate_id"].astype(str).unique())
        previous_ids = set(previous_df["candidate_id"].astype(str).unique())
        
        returning_ids = list(current_ids & previous_ids)
        new_ids = list(current_ids - previous_ids)
        
        metrics["returning_candidate_ids"] = returning_ids
        metrics["new_candidate_ids"] = new_ids
    
    return {
        "metrics": metrics,
    }
