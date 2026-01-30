"""
Analytics module for party stability vs volatility.
"""
from typing import Dict, Optional
import pandas as pd

from app.utils.metrics import compute_party_volatility


def analyze_party_volatility(
    current_df: pd.DataFrame,
    previous_df: Optional[pd.DataFrame] = None,
) -> Dict:
    """
    Analyze party stability vs volatility.
    
    Args:
        current_df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with party volatility analysis
    """
    metrics = compute_party_volatility(current_df, previous_df)
    
    return {
        "metrics": metrics,
    }
