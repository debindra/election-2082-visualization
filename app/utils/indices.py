"""
Utility functions for computing composite indices.
"""
from typing import Dict, List
import pandas as pd

def _exclude_independent_parties(party_series: pd.Series) -> pd.Series:
    """Return party series with स्वतन्त्र/Independent rows excluded (for unique_parties count)."""
    if party_series is None or len(party_series) == 0:
        return party_series
    s = party_series.astype(str).str.strip()
    lower = s.str.lower()
    mask = ~(
        s.isin(["स्वतन्त्र", "स्वतंत्र"])
        | lower.isin(["independent", "independent candidate", "independent (no party)"])
    )
    return party_series[mask]


def aggregate_metrics_by_geography(
    df: pd.DataFrame,
    geography_level: str = "province",
    include_candidate_ids: bool = True,
) -> List[Dict]:
    """
    Aggregate metrics by geography level (province, district, constituency).
    
    Args:
        df: Election DataFrame
        geography_level: One of 'province', 'district', 'constituency'
        include_candidate_ids: Whether to include list of candidate IDs
        
    Returns:
        List of dictionaries with aggregated metrics per geography unit
    """
    if geography_level not in df.columns:
        return []
    
    results = []
    
    for geo_unit in df[geography_level].unique():
        geo_df = df[df[geography_level] == geo_unit]
        
        metrics = {
            "name": geo_unit,
            "total_candidates": len(geo_df),
        }
        
        # Add candidate IDs if requested
        if include_candidate_ids and "candidate_id" in geo_df.columns:
            metrics["candidate_ids"] = geo_df["candidate_id"].astype(str).tolist()
        
        # Party distribution
        # unique_parties excludes स्वतन्त्र/Independent so parties + independents = total_candidates
        if "party" in geo_df.columns:
            parties_excl_indep = _exclude_independent_parties(geo_df["party"])
            metrics["unique_parties"] = int(parties_excl_indep.nunique()) if len(parties_excl_indep) > 0 else 0
            metrics["party_distribution"] = geo_df["party"].value_counts().to_dict()
        
        # Independent candidates (from is_independent or party=स्वतन्त्र)
        if "is_independent" in geo_df.columns:
            ind_sum = geo_df["is_independent"].fillna(False).astype(bool).sum()
        elif "party" in geo_df.columns:
            party_str = geo_df["party"].astype(str).str.strip()
            party_lower = party_str.str.lower()
            ind_sum = (
                party_str.isin(["स्वतन्त्र", "स्वतंत्र"])
                | party_lower.isin(["independent", "independent candidate", "independent (no party)"])
            ).sum()
        else:
            ind_sum = 0
        metrics["independent_count"] = int(ind_sum)
        n = len(geo_df)
        metrics["independent_percentage"] = round((ind_sum / n * 100), 2) if n > 0 else 0.0
        
        # Age statistics
        if "age" in geo_df.columns:
            ages = geo_df["age"].dropna()
            if len(ages) > 0:
                metrics["average_age"] = round(ages.mean(), 1)
                metrics["median_age"] = round(ages.median(), 1)
        
        # Gender distribution
        if "gender" in geo_df.columns:
            metrics["gender_distribution"] = geo_df["gender"].value_counts().to_dict()
        
        # Education distribution
        if "education_level" in geo_df.columns:
            metrics["education_distribution"] = geo_df["education_level"].value_counts().to_dict()
        
        # Number of nirbachan chetra (constituencies) in this unit.
        # At province level: constituency text (e.g. "निर्वाचन क्षेत्र 1") repeats across districts,
        # so count unique (district, constituency) pairs. At district level: nunique is correct.
        if "constituency" in geo_df.columns:
            if geography_level == "province" and "district" in geo_df.columns:
                metrics["constituency_count"] = int(geo_df.drop_duplicates(subset=["district", "constituency"]).shape[0])
            else:
                metrics["constituency_count"] = int(geo_df["constituency"].nunique())
        
        # Add parent geography if applicable
        if geography_level == "district" and "province" in geo_df.columns:
            metrics["province"] = geo_df["province"].iloc[0]
        elif geography_level == "constituency":
            if "district" in geo_df.columns:
                metrics["district"] = geo_df["district"].iloc[0]
            if "province" in geo_df.columns:
                metrics["province"] = geo_df["province"].iloc[0]
            # Use election_area_display for user-friendly name (e.g., "इलाम - १")
            if "election_area_display" in geo_df.columns:
                metrics["display_name"] = geo_df["election_area_display"].iloc[0]
        
        results.append(metrics)
    
    return results
