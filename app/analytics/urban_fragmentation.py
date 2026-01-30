"""
Analytics module for urban political fragmentation.
"""
from typing import Dict
import pandas as pd

from app.utils.metrics import compute_urban_fragmentation


def analyze_urban_fragmentation(current_df: pd.DataFrame) -> Dict:
    """
    Analyze urban political fragmentation.
    
    Args:
        current_df: Current election DataFrame
        
    Returns:
        Dictionary with urban fragmentation analysis
    """
    metrics = compute_urban_fragmentation(current_df)
    
    return {
        "metrics": metrics,
    }
