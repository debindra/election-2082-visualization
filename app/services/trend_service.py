"""
Service for computing trend analysis across elections.
"""
from typing import Dict, List, Optional
import pandas as pd
import logging

from app.data.loader import loader
from app.utils.metrics import (
    compute_independent_shift,
    compute_party_footprint,
    compute_age_trends,
    compute_education_evolution,
    compute_party_volatility,
    compute_candidate_density,
    compute_symbol_saturation,
    compute_political_churn,
    compute_gender_distribution,
)

logger = logging.getLogger(__name__)


def compute_trends(
    years: List[int],
    metric: Optional[str] = None,
) -> Dict:
    """
    Compute trends across multiple election years.
    
    Args:
        years: List of election years to analyze
        metric: Specific metric to compute (optional, computes all if None)
        
    Returns:
        Dictionary with trend data
    """
    # Load all election data
    election_data = {}
    for year in sorted(years):
        try:
            df, _ = loader.load_election(year)
            election_data[year] = df
        except Exception as e:
            logger.warning(f"Failed to load election {year}: {e}")
            continue
    
    if not election_data:
        raise ValueError("No election data available for trend analysis")
    
    trends = {}
    
    # Compute all metrics if not specified
    metrics_to_compute = [metric] if metric else [
        "independent_shift",
        "party_footprint",
        "age_trends",
        "education_evolution",
        "gender_evolution",
        "party_volatility",
        "candidate_density",
        "symbol_saturation",
        "political_churn",
    ]
    
    years_sorted = sorted(election_data.keys())
    
    for metric_name in metrics_to_compute:
        if metric_name == "independent_shift":
            trend_data = _compute_independent_trend(election_data, years_sorted)
            trends["independent_shift"] = trend_data
        elif metric_name == "party_footprint":
            trend_data = _compute_party_footprint_trend(election_data, years_sorted)
            trends["party_footprint"] = trend_data
        elif metric_name == "age_trends":
            trend_data = _compute_age_trend(election_data, years_sorted)
            trends["age_trends"] = trend_data
        elif metric_name == "education_evolution":
            trend_data = _compute_education_trend(election_data, years_sorted)
            trends["education_evolution"] = trend_data
        elif metric_name == "gender_evolution":
            trend_data = _compute_gender_evolution_trend(election_data, years_sorted)
            trends["gender_evolution"] = trend_data
        elif metric_name == "party_volatility":
            trend_data = _compute_party_volatility_trend(election_data, years_sorted)
            trends["party_volatility"] = trend_data
        elif metric_name == "candidate_density":
            trend_data = _compute_candidate_density_trend(election_data, years_sorted)
            trends["candidate_density"] = trend_data
        elif metric_name == "symbol_saturation":
            trend_data = _compute_symbol_saturation_trend(election_data, years_sorted)
            trends["symbol_saturation"] = trend_data
        elif metric_name == "political_churn":
            trend_data = _compute_political_churn_trend(election_data, years_sorted)
            trends["political_churn"] = trend_data
    
    return trends


def _compute_independent_trend(election_data: Dict[int, pd.DataFrame], years: List[int]) -> Dict:
    """Compute independent shift trend."""
    data_points = []
    for i, year in enumerate(years):
        df = election_data[year]
        prev_df = election_data[years[i-1]] if i > 0 else None
        metrics = compute_independent_shift(df, prev_df)
        data_points.append({
            "year": year,
            "value": metrics["independent_percentage"],
            "metadata": metrics,
        })
    return {
        "metric": "independent_shift",
        "data_points": data_points,
    }


def _compute_party_footprint_trend(election_data: Dict[int, pd.DataFrame], years: List[int]) -> Dict:
    """Compute party footprint trend."""
    data_points = []
    for i, year in enumerate(years):
        df = election_data[year]
        prev_df = election_data[years[i-1]] if i > 0 else None
        metrics = compute_party_footprint(df, prev_df)
        data_points.append({
            "year": year,
            "value": metrics["party_footprint_index"],
            "metadata": metrics,
        })
    return {
        "metric": "party_footprint",
        "data_points": data_points,
    }


def _compute_age_trend(election_data: Dict[int, pd.DataFrame], years: List[int]) -> Dict:
    """Compute age trend."""
    data_points = []
    for i, year in enumerate(years):
        df = election_data[year]
        prev_df = election_data[years[i-1]] if i > 0 else None
        metrics = compute_age_trends(df, prev_df)
        if metrics["average_age"]:
            data_points.append({
                "year": year,
                "value": metrics["average_age"],
                "metadata": metrics,
            })
    return {
        "metric": "age_trends",
        "data_points": data_points,
    }


def _compute_gender_evolution_trend(
    election_data: Dict[int, pd.DataFrame], years: List[int]
) -> Dict:
    """Compute female candidate percentage trend over years."""
    data_points = []
    for year in years:
        df = election_data[year]
        metrics = compute_gender_distribution(df)
        female_pct = metrics.get("female_percentage")
        if female_pct is not None:
            data_points.append({
                "year": year,
                "value": female_pct,
                "metadata": metrics,
            })
    return {
        "metric": "gender_evolution",
        "data_points": data_points,
    }


def _compute_education_trend(election_data: Dict[int, pd.DataFrame], years: List[int]) -> Dict:
    """Compute education evolution trend."""
    data_points = []
    for i, year in enumerate(years):
        df = election_data[year]
        prev_df = election_data[years[i-1]] if i > 0 else None
        metrics = compute_education_evolution(df, prev_df)
        if metrics["average_education_index"]:
            data_points.append({
                "year": year,
                "value": metrics["average_education_index"],
                "metadata": metrics,
            })
    return {
        "metric": "education_evolution",
        "data_points": data_points,
    }


def _compute_party_volatility_trend(election_data: Dict[int, pd.DataFrame], years: List[int]) -> Dict:
    """Compute party volatility trend."""
    data_points = []
    for i, year in enumerate(years):
        df = election_data[year]
        prev_df = election_data[years[i-1]] if i > 0 else None
        metrics = compute_party_volatility(df, prev_df)
        if metrics["party_volatility_index"] is not None:
            data_points.append({
                "year": year,
                "value": metrics["party_volatility_index"],
                "metadata": metrics,
            })
    return {
        "metric": "party_volatility",
        "data_points": data_points,
    }


def _compute_candidate_density_trend(election_data: Dict[int, pd.DataFrame], years: List[int]) -> Dict:
    """Compute candidate density trend."""
    from app.utils.metrics import compute_candidate_density
    data_points = []
    for year in years:
        df = election_data[year]
        metrics = compute_candidate_density(df)
        if metrics["candidate_density_index"]:
            data_points.append({
                "year": year,
                "value": metrics["candidate_density_index"],
                "metadata": metrics,
            })
    return {
        "metric": "candidate_density",
        "data_points": data_points,
    }


def _compute_symbol_saturation_trend(election_data: Dict[int, pd.DataFrame], years: List[int]) -> Dict:
    """Compute symbol saturation trend."""
    data_points = []
    for year in years:
        df = election_data[year]
        metrics = compute_symbol_saturation(df)
        if metrics["symbol_saturation_index"]:
            data_points.append({
                "year": year,
                "value": metrics["symbol_saturation_index"],
                "metadata": metrics,
            })
    return {
        "metric": "symbol_saturation",
        "data_points": data_points,
    }


def _compute_political_churn_trend(election_data: Dict[int, pd.DataFrame], years: List[int]) -> Dict:
    """Compute political churn trend."""
    data_points = []
    for i, year in enumerate(years):
        df = election_data[year]
        prev_df = election_data[years[i-1]] if i > 0 else None
        metrics = compute_political_churn(df, prev_df)
        if metrics["political_churn_index"] is not None:
            data_points.append({
                "year": year,
                "value": metrics["political_churn_index"],
                "metadata": metrics,
            })
    return {
        "metric": "political_churn",
        "data_points": data_points,
    }
