"""
Service for computing comprehensive insights for an election.
"""
from typing import Dict, Optional
import pandas as pd
import logging

from app.data.loader import loader
from app.analytics import (
    analyze_independent_shift,
    analyze_party_retrenchment,
    analyze_age_trends,
    analyze_urban_fragmentation,
    analyze_education_evolution,
    analyze_local_vs_outsider,
    analyze_party_volatility,
    analyze_candidate_density,
    analyze_symbol_saturation,
    analyze_political_churn,
)
from app.utils.metrics import compute_gender_distribution

logger = logging.getLogger(__name__)


def compute_insights(
    election_year: int,
    compare_with: Optional[int] = None,
) -> Dict:
    """
    Compute comprehensive insights for an election.
    
    Args:
        election_year: Election year to analyze
        compare_with: Optional year to compare with
        
    Returns:
        Dictionary with all insights
    """
    try:
        current_df, _ = loader.load_election(election_year)
    except Exception as e:
        logger.error(f"Failed to load election {election_year}: {e}")
        raise
    
    previous_df = None
    if compare_with:
        try:
            previous_df, _ = loader.load_election(compare_with)
        except Exception as e:
            logger.warning(f"Failed to load comparison election {compare_with}: {e}")
    
    insights = {}
    
    # Independent shift
    try:
        independent_analysis = analyze_independent_shift(current_df, previous_df)
        insights["independent_shift"] = {
            "name": "Independent Candidate Structural Shift",
            "value": independent_analysis["metrics"]["independent_percentage"],
            "description": "Percentage of independent candidates",
            "trend": "increasing" if independent_analysis["metrics"].get("shift_from_previous", 0) > 0 else "decreasing",
            "details": independent_analysis,
        }
    except Exception as e:
        logger.warning(f"Failed to compute independent shift: {e}")
    
    # Party retrenchment
    try:
        party_analysis = analyze_party_retrenchment(current_df, previous_df)
        insights["party_retrenchment"] = {
            "name": "Party Footprint Index",
            "value": party_analysis["metrics"]["party_footprint_index"],
            "description": "Average constituencies per party",
            "trend": party_analysis["metrics"].get("expansion_retrenchment", {}).get("trend"),
            "details": party_analysis,
        }
    except Exception as e:
        logger.warning(f"Failed to compute party retrenchment: {e}")
    
    # Age trends
    try:
        age_analysis = analyze_age_trends(current_df, previous_df)
        if age_analysis["metrics"]["average_age"]:
            insights["age_trends"] = {
                "name": "Candidate Age Trends",
                "value": age_analysis["metrics"]["average_age"],
                "description": "Average candidate age",
                "trend": age_analysis["metrics"].get("age_trend", {}).get("direction"),
                "details": age_analysis,
            }
    except Exception as e:
        logger.warning(f"Failed to compute age trends: {e}")
    
    # Gender gap
    try:
        gender_analysis = compute_gender_distribution(current_df)
        if gender_analysis.get("total_with_gender", 0) > 0:
            female_pct = gender_analysis.get("female_percentage")
            insights["gender_gap"] = {
                "name": "Female Candidate Representation",
                "value": female_pct,
                "description": "Percentage of female candidates",
                "trend": None,  # Could add comparison with previous year
                "details": gender_analysis,
            }
    except Exception as e:
        logger.warning(f"Failed to compute gender gap: {e}")
    
    # Urban fragmentation
    try:
        urban_analysis = analyze_urban_fragmentation(current_df)
        if urban_analysis["metrics"].get("urban_fragmentation_index"):
            insights["urban_fragmentation"] = {
                "name": "Urban Political Fragmentation",
                "value": urban_analysis["metrics"]["urban_fragmentation_index"],
                "description": "Parties per urban constituency",
                "trend": None,
                "details": urban_analysis,
            }
    except Exception as e:
        logger.warning(f"Failed to compute urban fragmentation: {e}")
    
    # Education evolution
    try:
        education_analysis = analyze_education_evolution(current_df, previous_df)
        if education_analysis["metrics"].get("average_education_index"):
            insights["education_evolution"] = {
                "name": "Education Profile Evolution",
                "value": education_analysis["metrics"]["average_education_index"],
                "description": "Average education index",
                "trend": education_analysis["metrics"].get("evolution", {}).get("direction"),
                "details": education_analysis,
            }
    except Exception as e:
        logger.warning(f"Failed to compute education evolution: {e}")
    
    # Local vs outsider
    try:
        local_analysis = analyze_local_vs_outsider(current_df)
        if local_analysis["metrics"].get("local_percentage") is not None:
            insights["local_vs_outsider"] = {
                "name": "Local vs Outsider Candidates",
                "value": local_analysis["metrics"]["local_percentage"],
                "description": "Percentage of local candidates",
                "trend": None,
                "details": local_analysis,
            }
    except Exception as e:
        logger.warning(f"Failed to compute local vs outsider: {e}")
    
    # Party volatility
    try:
        volatility_analysis = analyze_party_volatility(current_df, previous_df)
        if volatility_analysis["metrics"].get("party_volatility_index") is not None:
            insights["party_volatility"] = {
                "name": "Party Volatility Index",
                "value": volatility_analysis["metrics"]["party_volatility_index"],
                "description": "Party turnover percentage",
                "trend": None,
                "details": volatility_analysis,
            }
    except Exception as e:
        logger.warning(f"Failed to compute party volatility: {e}")
    
    # Candidate density
    try:
        density_analysis = analyze_candidate_density(current_df)
        if density_analysis["metrics"].get("candidate_density_index"):
            insights["candidate_density"] = {
                "name": "Candidate Density Index",
                "value": density_analysis["metrics"]["candidate_density_index"],
                "description": "Average candidates per constituency",
                "trend": None,
                "details": density_analysis,
            }
    except Exception as e:
        logger.warning(f"Failed to compute candidate density: {e}")
    
    # Symbol saturation
    try:
        symbol_analysis = analyze_symbol_saturation(current_df)
        if symbol_analysis["metrics"].get("symbol_saturation_index"):
            insights["symbol_saturation"] = {
                "name": "Symbol Saturation Index",
                "value": symbol_analysis["metrics"]["symbol_saturation_index"],
                "description": "Unique symbols per 100 candidates",
                "trend": None,
                "details": symbol_analysis,
            }
    except Exception as e:
        logger.warning(f"Failed to compute symbol saturation: {e}")
    
    # Political churn
    try:
        churn_analysis = analyze_political_churn(current_df, previous_df)
        if churn_analysis["metrics"].get("political_churn_index") is not None:
            insights["political_churn"] = {
                "name": "Political Churn Index",
                "value": churn_analysis["metrics"]["political_churn_index"],
                "description": "New candidate percentage",
                "trend": None,
                "details": churn_analysis,
            }
    except Exception as e:
        logger.warning(f"Failed to compute political churn: {e}")
    
    return {
        "election_year": election_year,
        "compare_with": compare_with,
        "insights": insights,
    }
