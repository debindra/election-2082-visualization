"""
Utility functions for computing election metrics.
"""
from typing import Dict, List, Optional
import pandas as pd
import numpy as np


def compute_independent_shift(df: pd.DataFrame, previous_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Compute independent candidate structural shift metrics.
    
    Args:
        df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with independent candidate metrics
    """
    if "is_independent" not in df.columns:
        return {
            "independent_count": 0,
            "independent_percentage": 0.0,
            "shift_from_previous": None,
        }
    
    independent_count = df["is_independent"].sum()
    total_candidates = len(df)
    independent_percentage = (independent_count / total_candidates * 100) if total_candidates > 0 else 0.0
    
    shift_from_previous = None
    if previous_df is not None and "is_independent" in previous_df.columns:
        prev_independent_count = previous_df["is_independent"].sum()
        prev_total = len(previous_df)
        prev_percentage = (prev_independent_count / prev_total * 100) if prev_total > 0 else 0.0
        shift_from_previous = independent_percentage - prev_percentage
    
    return {
        "independent_count": int(independent_count),
        "independent_percentage": round(independent_percentage, 2),
        "shift_from_previous": round(shift_from_previous, 2) if shift_from_previous is not None else None,
    }


def compute_party_footprint(df: pd.DataFrame, previous_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Compute Party Footprint Index (retrenchment vs expansion).
    
    Args:
        df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with party footprint metrics
    """
    if "party" not in df.columns:
        return {
            "unique_parties": 0,
            "party_footprint_index": 0.0,
            "expansion_retrenchment": None,
        }
    
    # Count unique parties
    unique_parties = df["party"].nunique()
    
    # Party footprint: average number of constituencies per party
    if "constituency" in df.columns:
        party_constituency_counts = df.groupby("party")["constituency"].nunique()
        footprint_index = party_constituency_counts.mean() if len(party_constituency_counts) > 0 else 0.0
    else:
        footprint_index = 0.0
    
    expansion_retrenchment = None
    if previous_df is not None and "party" in previous_df.columns and "constituency" in previous_df.columns:
        prev_unique_parties = previous_df["party"].nunique()
        prev_party_constituency_counts = previous_df.groupby("party")["constituency"].nunique()
        prev_footprint = prev_party_constituency_counts.mean() if len(prev_party_constituency_counts) > 0 else 0.0
        
        expansion_retrenchment = {
            "party_count_change": unique_parties - prev_unique_parties,
            "footprint_change": round(footprint_index - prev_footprint, 2),
            "trend": "expansion" if footprint_index > prev_footprint else "retrenchment",
        }
    
    return {
        "unique_parties": int(unique_parties),
        "party_footprint_index": round(footprint_index, 2),
        "expansion_retrenchment": expansion_retrenchment,
    }


def compute_age_trends(df: pd.DataFrame, previous_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Compute candidate age trends (leadership renewal).
    
    Args:
        df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with age trend metrics
    """
    if "age" not in df.columns:
        return {
            "average_age": None,
            "median_age": None,
            "age_trend": None,
        }
    
    ages = df["age"].dropna()
    
    result = {
        "average_age": round(ages.mean(), 1) if len(ages) > 0 else None,
        "median_age": round(ages.median(), 1) if len(ages) > 0 else None,
        "age_trend": None,
    }
    
    if previous_df is not None and "age" in previous_df.columns:
        prev_ages = previous_df["age"].dropna()
        if len(prev_ages) > 0:
            prev_avg = prev_ages.mean()
            current_avg = ages.mean() if len(ages) > 0 else None
            
            if current_avg is not None:
                age_change = current_avg - prev_avg
                result["age_trend"] = {
                    "change": round(age_change, 1),
                    "direction": "younger" if age_change < 0 else "older",
                }
    
    return result


def compute_urban_fragmentation(df: pd.DataFrame) -> Dict:
    """
    Compute urban political fragmentation metrics.
    
    Note: This assumes urban districts can be identified by name patterns
    or would need a separate urban/rural classification column.
    
    Args:
        df: Current election DataFrame
        
    Returns:
        Dictionary with urban fragmentation metrics
    """
    if "district" not in df.columns or "constituency" not in df.columns:
        return {
            "urban_fragmentation_index": None,
            "urban_districts": [],
        }
    
    # Common urban district patterns in Nepal (Kathmandu, Lalitpur, Bhaktapur, Pokhara, etc.)
    urban_keywords = ["kathmandu", "lalitpur", "bhaktapur", "pokhara", "biratnagar", "birgunj"]
    
    df_lower = df.copy()
    df_lower["district_lower"] = df_lower["district"].astype(str).str.lower()
    
    urban_mask = df_lower["district_lower"].str.contains("|".join(urban_keywords), na=False)
    urban_df = df[urban_mask]
    
    if len(urban_df) == 0:
        return {
            "urban_fragmentation_index": None,
            "urban_districts": [],
        }
    
    # Fragmentation: number of parties per urban constituency
    if "party" in urban_df.columns:
        urban_districts = urban_df["district"].unique().tolist()
        party_per_constituency = urban_df.groupby("constituency")["party"].nunique().mean()
        
        return {
            "urban_fragmentation_index": round(party_per_constituency, 2),
            "urban_districts": urban_districts,
        }
    
    return {
        "urban_fragmentation_index": None,
        "urban_districts": [],
    }


def compute_education_evolution(df: pd.DataFrame, previous_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Compute education profile evolution.
    
    Args:
        df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with education metrics
    """
    if "education_level" not in df.columns:
        return {
            "education_distribution": {},
            "average_education_index": None,
            "evolution": None,
        }
    
    education_counts = df["education_level"].value_counts().to_dict()
    
    # Simple education index (higher = more educated)
    # This is a simplified mapping - adjust based on actual education levels
    education_weights = {
        "phd": 5,
        "masters": 4,
        "bachelors": 3,
        "intermediate": 2,
        "slc": 1,
        "below slc": 0,
    }
    
    education_values = []
    for level in df["education_level"].dropna():
        level_lower = str(level).lower()
        weight = next((w for k, w in education_weights.items() if k in level_lower), 2)
        education_values.append(weight)
    
    avg_education_index = np.mean(education_values) if education_values else None
    
    evolution = None
    if previous_df is not None and "education_level" in previous_df.columns:
        prev_education_values = []
        for level in previous_df["education_level"].dropna():
            level_lower = str(level).lower()
            weight = next((w for k, w in education_weights.items() if k in level_lower), 2)
            prev_education_values.append(weight)
        
        prev_avg = np.mean(prev_education_values) if prev_education_values else None
        
        if avg_education_index is not None and prev_avg is not None:
            evolution = {
                "change": round(avg_education_index - prev_avg, 2),
                "direction": "more_educated" if avg_education_index > prev_avg else "less_educated",
            }
    
    return {
        "education_distribution": education_counts,
        "average_education_index": round(avg_education_index, 2) if avg_education_index else None,
        "evolution": evolution,
    }


def compute_local_vs_outsider(df: pd.DataFrame) -> Dict:
    """
    Compute local vs outsider candidate trend.
    
    Compares birth_district with election district.
    
    Args:
        df: Current election DataFrame
        
    Returns:
        Dictionary with local/outsider metrics
    """
    if "birth_district" not in df.columns or "district" not in df.columns:
        return {
            "local_candidates": None,
            "outsider_candidates": None,
            "local_percentage": None,
        }
    
    # Compare birth_district with district
    df_clean = df[df["birth_district"].notna() & df["district"].notna()].copy()
    
    if len(df_clean) == 0:
        return {
            "local_candidates": None,
            "outsider_candidates": None,
            "local_percentage": None,
        }
    
    df_clean["is_local"] = (
        df_clean["birth_district"].astype(str).str.lower().str.strip() ==
        df_clean["district"].astype(str).str.lower().str.strip()
    )
    
    local_count = df_clean["is_local"].sum()
    outsider_count = (~df_clean["is_local"]).sum()
    total = len(df_clean)
    
    return {
        "local_candidates": int(local_count),
        "outsider_candidates": int(outsider_count),
        "local_percentage": round((local_count / total * 100), 2) if total > 0 else None,
    }


def compute_party_volatility(df: pd.DataFrame, previous_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Compute party stability vs volatility.
    
    Args:
        df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with party volatility metrics
    """
    if "party" not in df.columns:
        return {
            "party_volatility_index": None,
            "stable_parties": [],
            "new_parties": [],
        }
    
    current_parties = set(df["party"].unique())
    
    if previous_df is None or "party" not in previous_df.columns:
        return {
            "party_volatility_index": None,
            "stable_parties": list(current_parties),
            "new_parties": [],
        }
    
    previous_parties = set(previous_df["party"].unique())
    
    stable_parties = list(current_parties & previous_parties)
    new_parties = list(current_parties - previous_parties)
    disappeared_parties = list(previous_parties - current_parties)
    
    total_unique_parties = len(current_parties | previous_parties)
    volatility_index = (
        (len(new_parties) + len(disappeared_parties)) / total_unique_parties * 100
        if total_unique_parties > 0 else 0.0
    )
    
    return {
        "party_volatility_index": round(volatility_index, 2),
        "stable_parties": stable_parties,
        "new_parties": new_parties,
        "disappeared_parties": disappeared_parties,
    }


def compute_candidate_density(df: pd.DataFrame) -> Dict:
    """
    Compute candidate density vs voter choice metrics.
    
    Args:
        df: Current election DataFrame
        
    Returns:
        Dictionary with candidate density metrics
    """
    if "constituency" not in df.columns:
        return {
            "average_candidates_per_constituency": None,
            "candidate_density_index": None,
        }
    
    candidates_per_constituency = df.groupby("constituency").size()
    avg_candidates = candidates_per_constituency.mean()
    
    # Density index: higher = more choice
    density_index = avg_candidates
    
    return {
        "average_candidates_per_constituency": round(avg_candidates, 2),
        "candidate_density_index": round(density_index, 2),
    }


def compute_symbol_saturation(df: pd.DataFrame) -> Dict:
    """
    Compute symbol saturation (ballot UX metric).
    
    Args:
        df: Current election DataFrame
        
    Returns:
        Dictionary with symbol saturation metrics
    """
    if "symbol" not in df.columns:
        return {
            "unique_symbols": None,
            "symbol_saturation_index": None,
        }
    
    unique_symbols = df["symbol"].nunique()
    total_candidates = len(df)
    
    # Saturation: unique symbols per 100 candidates
    saturation_index = (unique_symbols / total_candidates * 100) if total_candidates > 0 else 0.0
    
    return {
        "unique_symbols": int(unique_symbols),
        "symbol_saturation_index": round(saturation_index, 2),
    }


def compute_political_churn(df: pd.DataFrame, previous_df: Optional[pd.DataFrame] = None) -> Dict:
    """
    Compute Political Churn Index (candidate turnover).
    
    Args:
        df: Current election DataFrame
        previous_df: Previous election DataFrame for comparison
        
    Returns:
        Dictionary with political churn metrics
    """
    if "candidate_id" not in df.columns:
        return {
            "political_churn_index": None,
            "returning_candidates": None,
            "new_candidates": None,
        }
    
    current_candidate_ids = set(df["candidate_id"].astype(str).unique())
    
    if previous_df is None or "candidate_id" not in previous_df.columns:
        return {
            "political_churn_index": None,
            "returning_candidates": None,
            "new_candidates": len(current_candidate_ids),
        }
    
    previous_candidate_ids = set(previous_df["candidate_id"].astype(str).unique())
    
    returning_candidates = len(current_candidate_ids & previous_candidate_ids)
    new_candidates = len(current_candidate_ids - previous_candidate_ids)
    total_unique = len(current_candidate_ids | previous_candidate_ids)
    
    churn_index = (new_candidates / total_unique * 100) if total_unique > 0 else 0.0
    
    return {
        "political_churn_index": round(churn_index, 2),
        "returning_candidates": int(returning_candidates),
        "new_candidates": int(new_candidates),
    }


def compute_independent_vote_share_by_district(df: pd.DataFrame) -> Dict:
    """
    Compute independent candidate strength by district.

    Prefers vote-based share (independent votes / total votes) when
    `votes_received` is available, otherwise falls back to simple
    candidate share (independent candidates / total candidates).

    Returns:
        {
          "method": "votes" | "candidates",
          "districts": [
             {
               "district": str,
               "independent_vote_share": float | None,      # 0-100
               "independent_candidate_share": float | None, # 0-100
               "total_votes": float | None,
               "total_candidates": int
             },
             ...
          ]
        }
    """
    if "district" not in df.columns or "is_independent" not in df.columns:
        return {"method": "unknown", "districts": []}

    has_votes = "votes_received" in df.columns and df["votes_received"].notna().any()
    method = "votes" if has_votes else "candidates"

    results = []
    grouped = df.groupby("district", dropna=False)

    for district, g in grouped:
        total_candidates = int(len(g))
        indep_mask = g["is_independent"] == True
        independent_candidates = int(indep_mask.sum())

        independent_candidate_share = (
            round(independent_candidates / total_candidates * 100, 2)
            if total_candidates > 0
            else None
        )

        total_votes = None
        independent_vote_share = None

        if has_votes:
            votes = g["votes_received"].fillna(0)
            total_votes_val = float(votes.sum())
            total_votes = total_votes_val if total_votes_val > 0 else None

            if total_votes:
                indep_votes = float(votes[indep_mask].sum())
                independent_vote_share = round(indep_votes / total_votes * 100, 2)

        results.append(
            {
                "district": str(district) if district is not None else "",
                "independent_vote_share": independent_vote_share,
                "independent_candidate_share": independent_candidate_share,
                "total_votes": total_votes,
                "total_candidates": total_candidates,
            }
        )

    return {"method": method, "districts": results}


def compute_competition_pressure_by_district(df: pd.DataFrame) -> Dict:
    """
    Compute district-level competition pressure.

    For each constituency, computes the vote-share gap between the top
    2–3 candidates, then aggregates (average) those gaps at district level.

    Uses `votes_received` when available, otherwise falls back to equal
    weights per candidate.

    Returns:
        {
          "districts": [
             {
               "district": str,
               "avg_margin_top2": float | None,  # in percentage points
               "avg_margin_top3": float | None   # in percentage points
             },
             ...
          ]
        }
    """
    if "district" not in df.columns:
        return {"districts": []}

    has_votes = "votes_received" in df.columns and df["votes_received"].notna().any()

    # Work at constituency level when available, otherwise district level only
    group_cols = ["district", "constituency"] if "constituency" in df.columns else ["district"]

    rows = []

    for keys, g in df.groupby(group_cols, dropna=False):
        if isinstance(keys, tuple):
            district = keys[0]
        else:
            district = keys

        if has_votes:
            votes = g["votes_received"].fillna(0)
            total_votes = float(votes.sum())
            if total_votes <= 0:
                continue
            shares = (
                votes.sort_values(ascending=False) / total_votes * 100.0
                if len(votes) > 0
                else pd.Series([], dtype=float)
            )
        else:
            n = len(g)
            if n == 0:
                continue
            # Equal share if no vote data
            shares = pd.Series([100.0 / n] * n)

        if len(shares) == 0:
            continue

        shares_sorted = shares.sort_values(ascending=False).reset_index(drop=True)
        top1 = float(shares_sorted.iloc[0])
        top2 = float(shares_sorted.iloc[1]) if len(shares_sorted) > 1 else 0.0
        top3 = float(shares_sorted.iloc[2]) if len(shares_sorted) > 2 else 0.0

        margin_1_2 = top1 - top2
        margin_1_3 = top1 - top3

        rows.append(
            {
                "district": str(district) if district is not None else "",
                "margin_1_2": margin_1_2,
                "margin_1_3": margin_1_3,
            }
        )

    if not rows:
        return {"districts": []}

    tmp = pd.DataFrame(rows)
    agg = (
        tmp.groupby("district", dropna=False)[["margin_1_2", "margin_1_3"]]
        .mean()
        .reset_index()
    )

    districts = []
    for _, r in agg.iterrows():
        districts.append(
            {
                "district": str(r["district"]) if r["district"] is not None else "",
                "avg_margin_top2": round(float(r["margin_1_2"]), 2),
                "avg_margin_top3": round(float(r["margin_1_3"]), 2),
            }
        )

    return {"districts": districts}


def compute_district_competition_intensity(
    df: pd.DataFrame,
    top_n: int = 15,
) -> Dict:
    """
    District-level competition intensity: top districts by number of candidates,
    with breakdown by party for stacked visualization.

    Returns:
        {
          "top_districts": [
            {
              "district": str,
              "total_candidates": int,
              "by_party": [{"party": str, "count": int}, ...],
            },
            ...
          ]
        }
    """
    if "district" not in df.columns:
        return {"top_districts": []}

    party_col = "party" if "party" in df.columns else None

    # Count candidates per district (and per party within district)
    if party_col:
        grp = df.groupby(["district", party_col], dropna=False).size().reset_index(name="count")
        rows = []
        for _, r in grp.iterrows():
            district = str(r["district"]) if r["district"] is not None else ""
            party = str(r[party_col]) if r[party_col] is not None else ""
            count = int(r["count"])
            rows.append({"district": district, "party": party, "count": count})
        if not rows:
            return {"top_districts": []}
        by_district = {}
        for row in rows:
            d = row["district"]
            if d not in by_district:
                by_district[d] = {"total_candidates": 0, "by_party": []}
            by_district[d]["total_candidates"] += row["count"]
            by_district[d]["by_party"].append({"party": row["party"], "count": row["count"]})
    else:
        district_totals = df.groupby("district", dropna=False).size().reset_index(name="total_candidates")
        by_district = {}
        for _, r in district_totals.iterrows():
            d = str(r["district"]) if r["district"] is not None else ""
            total = int(r["total_candidates"])
            by_district[d] = {"total_candidates": total, "by_party": [{"party": "All", "count": total}]}

    # Sort by total_candidates descending and take top_n
    sorted_districts = sorted(
        by_district.items(),
        key=lambda x: x[1]["total_candidates"],
        reverse=True,
    )[:top_n]

    top_districts = []
    for district, data in sorted_districts:
        by_party = sorted(data["by_party"], key=lambda p: p["count"], reverse=True)
        top_districts.append(
            {
                "district": district,
                "total_candidates": data["total_candidates"],
                "by_party": by_party,
            }
        )

    return {"top_districts": top_districts}


def compute_party_saturation(df: pd.DataFrame) -> Dict:
    """
    Compute party saturation vs reach metrics.

    For each party, counts number of candidates, seats contested
    (unique constituencies), and seats won (winner rows), and derives
    a simple win rate.

    Returns:
        {
          "parties": [
            {
              "party": str,
              "candidates": int,
              "seats_contested": int | None,
              "seats_won": int | None,
              "win_rate": float | None,  # 0-100
            },
            ...
          ]
        }
    """
    if "party" not in df.columns:
        return {"parties": []}

    group = df.groupby("party", dropna=False)
    parties = []

    for party, g in group:
        candidates = int(len(g))

        seats_contested = None
        if "constituency" in g.columns:
            seats_contested = int(g["constituency"].nunique())

        seats_won = None
        if "is_winner" in g.columns:
            # Booleans may be stored as 0/1 or True/False
            seats_won = int((g["is_winner"] == True).sum())

        win_rate = None
        if seats_contested and seats_contested > 0 and seats_won is not None:
            win_rate = round(seats_won / seats_contested * 100.0, 2)

        parties.append(
            {
                "party": str(party) if party is not None else "",
                "candidates": candidates,
                "seats_contested": seats_contested,
                "seats_won": seats_won,
                "win_rate": win_rate,
            }
        )

    return {"parties": parties}


def _is_independent_party(party_series: pd.Series) -> pd.Series:
    """Return boolean series: True where party is independent (स्वतन्त्र / Independent)."""
    if party_series is None or len(party_series) == 0:
        return pd.Series(dtype=bool)
    s = party_series.astype(str).str.strip()
    lower = s.str.lower()
    return (
        s.isin(["स्वतन्त्र", "स्वतंत्र"])
        | lower.isin(["independent", "independent candidate", "independent (no party)"])
    )


def compute_age_gap_by_movement(df: pd.DataFrame) -> Dict:
    """
    Compute average age by political movement: top 3 legacy parties, new/alternative
    parties, and independents.

    Legacy = top 3 parties by candidate count (excluding independents).
    New/alternative = all other non-independent parties.
    Independents = is_independent or party name स्वतन्त्र / Independent.

    Power insight: "Youth participation is rising — but mostly outside traditional parties."

    Returns:
        {
          "election_year": int (optional, if passed),
          "top3_legacy": {
            "average_age": float | None,
            "parties": [str],
            "candidate_count": int,
          },
          "new_alternative": {
            "average_age": float | None,
            "candidate_count": int,
          },
          "independents": {
            "average_age": float | None,
            "candidate_count": int,
          },
          "power_insight": str,
        }
    """
    if "age" not in df.columns:
        return {
            "top3_legacy": {"average_age": None, "parties": [], "candidate_count": 0},
            "new_alternative": {"average_age": None, "candidate_count": 0},
            "independents": {"average_age": None, "candidate_count": 0},
            "power_insight": "Youth participation is rising — but mostly outside traditional parties.",
        }

    # Identify independents: column is_independent or party name
    if "is_independent" in df.columns:
        indep_mask = df["is_independent"] == True
    elif "party" in df.columns:
        indep_mask = _is_independent_party(df["party"])
    else:
        indep_mask = pd.Series(False, index=df.index)

    independents_df = df[indep_mask]
    non_indep_df = df[~indep_mask]

    def avg_age(sub_df: pd.DataFrame) -> Optional[float]:
        ages = sub_df["age"].dropna()
        if len(ages) == 0:
            return None
        return round(float(ages.mean()), 1)

    # Top 3 legacy parties = top 3 by candidate count among non-independents
    top3_legacy_parties = []
    top3_legacy_avg_age = None
    top3_legacy_count = 0

    if "party" in non_indep_df.columns and len(non_indep_df) > 0:
        party_counts = non_indep_df.groupby("party", dropna=False).size().sort_values(ascending=False)
        top3_names = party_counts.head(3).index.tolist()
        top3_legacy_parties = [str(p) for p in top3_names if p is not None and str(p).strip()]
        top3_mask = non_indep_df["party"].isin(top3_names)
        top3_df = non_indep_df[top3_mask]
        top3_legacy_count = int(len(top3_df))
        top3_legacy_avg_age = avg_age(top3_df)

    # New/alternative = non-independent, not in top 3
    new_alt_df = non_indep_df
    if top3_legacy_parties and "party" in new_alt_df.columns:
        new_alt_df = new_alt_df[~new_alt_df["party"].isin(top3_legacy_parties)]
    new_alt_count = int(len(new_alt_df))
    new_alt_avg_age = avg_age(new_alt_df) if len(new_alt_df) > 0 else None

    # Independents
    indep_count = int(len(independents_df))
    indep_avg_age = avg_age(independents_df) if len(independents_df) > 0 else None

    return {
        "top3_legacy": {
            "average_age": top3_legacy_avg_age,
            "parties": top3_legacy_parties,
            "candidate_count": top3_legacy_count,
        },
        "new_alternative": {
            "average_age": new_alt_avg_age,
            "candidate_count": new_alt_count,
        },
        "independents": {
            "average_age": indep_avg_age,
            "candidate_count": indep_count,
        },
        "power_insight": "Youth participation is rising — but mostly outside traditional parties.",
    }


# --- Year insights (filtered by party / province / district) ---

AGE_BANDS = [
    ("25-34", 25, 35),
    ("35-44", 35, 45),
    ("45-54", 45, 55),
    ("55-64", 55, 65),
    ("65+", 65, 150),
]


def compute_age_demographics(df: pd.DataFrame) -> Dict:
    """
    Age demographics of candidates for visualization.
    Returns count and percentage per age band (25-34, 35-44, 45-54, 55-64, 65+).
    """
    if "age" not in df.columns:
        return {"bands": [], "average_age": None, "median_age": None, "total_with_age": 0}

    ages = df["age"].dropna()
    total = len(ages)
    if total == 0:
        return {"bands": [], "average_age": None, "median_age": None, "total_with_age": 0}

    band_counts = {label: 0 for label, _, _ in AGE_BANDS}
    for age in ages:
        for label, lo, hi in AGE_BANDS:
            if lo <= age < hi:
                band_counts[label] += 1
                break

    bands = [
        {
            "band": label,
            "count": band_counts[label],
            "percentage": round(band_counts[label] / total * 100, 2),
        }
        for label, _, _ in AGE_BANDS
    ]

    return {
        "bands": bands,
        "average_age": round(float(ages.mean()), 1),
        "median_age": round(float(ages.median()), 1),
        "total_with_age": int(total),
    }


# Weights for Academic Qualification Generalized (visualization only)
EDUCATION_GENERALIZED_WEIGHTS = {
    "no formal education": 0,
    "illiterate": 0,
    "n/a": 0,
    "slc": 1,
    "see": 1,
    "slc / see": 1,
    "10+2": 2,
    "intermediate": 2,
    "bachelor": 3,
    "graduate": 3,
    "masters": 4,
    "master": 4,
    "phd": 5,
    "doctorate": 5,
}

# Fallback weights for raw education_level (when generalized column absent)
EDUCATION_LEVEL_WEIGHTS = {
    "phd": 5,
    "masters": 4,
    "bachelors": 3,
    "intermediate": 2,
    "slc": 1,
    "below slc": 0,
}


def _weight_for_generalized(level: str) -> int:
    """Map Academic Qualification Generalized label to numeric weight (0-5)."""
    level_lower = str(level).lower().strip()
    for key, w in EDUCATION_GENERALIZED_WEIGHTS.items():
        if key in level_lower or level_lower == key:
            return w
    # Default for unknown (e.g. "Engineering Graduate" -> treat as bachelor-level)
    if "graduate" in level_lower or "bachelor" in level_lower:
        return 3
    if "master" in level_lower:
        return 4
    if "phd" in level_lower or "doctorate" in level_lower:
        return 5
    if "slc" in level_lower or "see" in level_lower or "10+2" in level_lower:
        return 2
    return 2  # default intermediate


def compute_education_profile(df: pd.DataFrame) -> Dict:
    """
    Education profile insight: distribution by education level and average index.

    Uses "Academic Qualification Generalized" when present (for chart visualization);
    otherwise falls back to education_level (raw qualification).
    """
    use_generalized = "academic_qualification_generalized" in df.columns
    source_col = "academic_qualification_generalized" if use_generalized else "education_level"

    if source_col not in df.columns:
        return {"distribution": [], "average_index": None, "total_with_education": 0}

    weights_map = EDUCATION_GENERALIZED_WEIGHTS if use_generalized else EDUCATION_LEVEL_WEIGHTS

    counts = df[source_col].value_counts(dropna=False)
    total = len(
        df[df[source_col].notna() & (df[source_col].astype(str).str.strip() != "")]
    )
    if total == 0:
        return {"distribution": [], "average_index": None, "total_with_education": 0}

    distribution = []
    weighted_sum = 0.0
    weighted_n = 0
    for level, count in counts.items():
        if pd.isna(level) or str(level).strip() == "":
            continue
        level_str = str(level).strip()
        if use_generalized:
            weight = _weight_for_generalized(level_str)
        else:
            level_lower = level_str.lower()
            weight = next(
                (w for k, w in EDUCATION_LEVEL_WEIGHTS.items() if k in level_lower), 2
            )
        pct = round(count / total * 100, 2)
        distribution.append({"level": level_str, "count": int(count), "percentage": pct})
        weighted_sum += weight * count
        weighted_n += count

    avg_index = round(weighted_sum / weighted_n, 2) if weighted_n > 0 else None
    return {
        "distribution": distribution,
        "average_index": avg_index,
        "total_with_education": int(total),
    }


def compute_party_vs_age(df: pd.DataFrame) -> Dict:
    """
    Party vs age trend (power insight): average age per party.
    """
    if "party" not in df.columns or "age" not in df.columns:
        return {"parties": [], "power_insight": "Select party/state/district to see age trends."}

    parties_list = []
    for party, g in df.groupby("party", dropna=False):
        if party is None or str(party).strip() == "":
            continue
        ages = g["age"].dropna()
        avg_age = round(float(ages.mean()), 1) if len(ages) > 0 else None
        parties_list.append({
            "party": str(party).strip(),
            "average_age": avg_age,
            "candidate_count": int(len(g)),
        })

    parties_list.sort(key=lambda x: (x["average_age"] or 0, -x["candidate_count"]))
    youngest = next((p for p in parties_list if p["average_age"] is not None), None)
    oldest = next((p for p in reversed(parties_list) if p["average_age"] is not None), None)
    power_insight = "Youth participation is rising — but mostly outside traditional parties."
    if youngest and oldest and youngest != oldest:
        power_insight = f"Youngest cohort: {youngest['party']} (avg {youngest['average_age']} yrs). Oldest: {oldest['party']} (avg {oldest['average_age']} yrs)."

    return {"parties": parties_list, "power_insight": power_insight}


def compute_gender_distribution(df: pd.DataFrame) -> Dict:
    """
    Gender distribution of candidates: M/F/Other counts, female %, gender parity index.
    """
    if "gender" not in df.columns:
        return {
            "distribution": [],
            "female_percentage": None,
            "gender_parity_index": None,
            "total_with_gender": 0,
            "power_insight": "No gender data available.",
        }
    g = df["gender"].dropna()
    total = len(g)
    if total == 0:
        return {
            "distribution": [],
            "female_percentage": None,
            "gender_parity_index": None,
            "total_with_gender": 0,
            "power_insight": "No gender data available.",
        }
    counts = g.value_counts()
    distribution = [
        {"gender": str(k), "count": int(v), "percentage": round(float(v) / total * 100, 2)}
        for k, v in counts.items()
    ]
    female_count = int(counts.get("F", 0) + counts.get("Female", 0))
    female_pct = round(float(female_count / total * 100), 2) if total > 0 else None
    male_count = int(counts.get("M", 0) + counts.get("Male", 0))
    gender_parity = None
    if total > 0 and (female_count + male_count) > 0:
        min_share = min(female_count, male_count) / total * 100
        gender_parity = round(min_share / 50.0, 2)  # 1.0 = perfect parity
        gender_parity = min(1.0, max(0.0, gender_parity))
    power_insight = f"Female representation: {female_pct}% of candidates."
    if gender_parity is not None:
        if gender_parity < 0.2:
            power_insight += " Gender parity remains a significant gap."
        elif gender_parity < 0.5:
            power_insight += " Modest progress toward gender balance."
        else:
            power_insight += " Strong progress toward gender balance."
    return {
        "distribution": distribution,
        "female_percentage": female_pct,
        "gender_parity_index": gender_parity,
        "total_with_gender": total,
        "power_insight": power_insight,
    }


def compute_party_vs_gender(df: pd.DataFrame, top_n: int = 15) -> Dict:
    """
    Party vs gender: female candidate share per party (power insight).
    """
    if "party" not in df.columns or "gender" not in df.columns:
        return {"parties": [], "power_insight": "Select party/state/district to see gender representation."}
    parties_list = []
    for party, g in df.groupby("party", dropna=False):
        if party is None or str(party).strip() == "":
            continue
        total_p = len(g)
        female_count = (g["gender"].fillna("").astype(str).str.upper().isin(["F", "FEMALE"])).sum()
        female_pct = round(float(female_count / total_p * 100), 2) if total_p > 0 else None
        parties_list.append({
            "party": str(party).strip(),
            "female_count": int(female_count),
            "female_percentage": female_pct,
            "candidate_count": int(total_p),
        })
    parties_list.sort(key=lambda x: (x["female_percentage"] or 0, -x["candidate_count"]), reverse=True)
    top_female = next((p for p in parties_list if (p["female_percentage"] or 0) > 0), None)
    power_insight = "Gender representation varies widely across parties."
    if top_female:
        power_insight = f"Highest female share: {top_female['party']} ({top_female['female_percentage']}% female candidates)."
    return {"parties": parties_list[:top_n], "power_insight": power_insight}


def compute_birthplace_vs_contest(df: pd.DataFrame) -> Dict:
    """
    Birthplace vs contest district (local representation).
    """
    if "birth_district" not in df.columns or "district" not in df.columns:
        return {"local_count": 0, "outsider_count": 0, "local_percentage": None, "unknown_count": 0}

    df_clean = df[df["birth_district"].notna() & df["district"].notna()].copy()
    df_clean["birth_d"] = df_clean["birth_district"].astype(str).str.lower().str.strip()
    df_clean["contest_d"] = df_clean["district"].astype(str).str.lower().str.strip()
    df_clean["is_local"] = df_clean["birth_d"] == df_clean["contest_d"]

    local_count = int(df_clean["is_local"].sum())
    outsider_count = int((~df_clean["is_local"]).sum())
    total = local_count + outsider_count
    unknown_count = int(len(df) - len(df_clean))

    return {
        "local_count": local_count,
        "outsider_count": outsider_count,
        "local_percentage": round(local_count / total * 100, 2) if total > 0 else None,
        "unknown_count": unknown_count,
        "total_with_birthplace": total,
    }


def compute_symbol_recognition(df: pd.DataFrame, top_n: int = 15) -> Dict:
    """
    Symbol recognition analysis (UX insight): top symbols by candidate count, saturation.
    """
    if "symbol" not in df.columns:
        return {"symbols": [], "unique_symbols": 0, "saturation_index": None, "ux_insight": "No symbol data."}

    total = len(df)
    symbol_counts = df["symbol"].value_counts(dropna=False)
    unique = df["symbol"].nunique()
    saturation = round(unique / total * 100, 2) if total > 0 else 0.0

    symbols = []
    for sym, count in symbol_counts.head(top_n).items():
        if pd.isna(sym) or str(sym).strip() == "":
            continue
        party_name = None
        if "party" in df.columns:
            subset = df[df["symbol"].astype(str).str.strip() == str(sym).strip()]
            if len(subset) > 0:
                if "party_en" in df.columns and subset["party_en"].notna().any():
                    party_name = subset["party_en"].mode().iloc[0]
                else:
                    party_name = subset["party"].mode().iloc[0]
                if pd.notna(party_name):
                    party_name = str(party_name).strip()
                else:
                    party_name = None
        symbols.append({
            "symbol": str(sym).strip(),
            "candidate_count": int(count),
            "percentage": round(count / total * 100, 2),
            "party_name": party_name,
        })

    ux_insight = f"Ballot complexity: {unique} unique symbols for {total} candidates ({saturation} symbols per 100 candidates)."
    return {
        "symbols": symbols,
        "unique_symbols": int(unique),
        "saturation_index": saturation,
        "ux_insight": ux_insight,
    }


def compute_composite_metrics(df: pd.DataFrame) -> Dict:
    """
    High-value composite metrics for smart voters.
    """
    total = len(df)
    if total == 0:
        return {"candidate_count": 0, "smart_voter_summary": "No candidates in selection."}

    # Vote share (average among those with data)
    avg_vote_share = None
    if "votes_percentage" in df.columns:
        v = df["votes_percentage"].dropna()
        avg_vote_share = round(float(v.mean()), 2) if len(v) > 0 else None
    elif "vote_share_in_race" in df.columns:
        v = df["vote_share_in_race"].dropna()
        avg_vote_share = round(float(v.mean()), 2) if len(v) > 0 else None

    # Margin (winners)
    avg_margin = None
    if "margin" in df.columns:
        margins = df[df["margin"].notna()]["margin"]
        avg_margin = round(float(margins.mean()), 2) if len(margins) > 0 else None

    # Education index (reuse weights)
    education_index = None
    if "education_level" in df.columns:
        education_weights = {"phd": 5, "masters": 4, "bachelors": 3, "intermediate": 2, "slc": 1, "below slc": 0}
        vals = []
        for level in df["education_level"].dropna():
            level_lower = str(level).lower()
            w = next((w for k, w in education_weights.items() if k in level_lower), 2)
            vals.append(w)
        education_index = round(float(np.mean(vals)), 2) if vals else None

    # Local %
    local_pct = None
    if "birth_district" in df.columns and "district" in df.columns:
        local_analysis = compute_local_vs_outsider(df)
        local_pct = local_analysis.get("local_percentage")

    # Symbol coverage (unique symbols / candidates)
    symbol_coverage = None
    if "symbol" in df.columns:
        symbol_coverage = round(df["symbol"].nunique() / total * 100, 2)

    # Winner share
    winner_count = None
    if "is_winner" in df.columns:
        winner_count = int((df["is_winner"] == True).sum())

    # Party Fragmentation Score (0–100): Herfindahl-based; higher = more fragmented
    party_fragmentation_score = None
    if "party" in df.columns and total > 0:
        party_counts = df["party"].fillna("_unknown").value_counts()
        shares = party_counts / total
        herfindahl = (shares ** 2).sum()
        party_fragmentation_score = round(float((1 - herfindahl) * 100), 2)
        party_fragmentation_score = min(100, max(0, party_fragmentation_score))

    # Youth Representation Score (0–100): share of candidates with age data who are under 40
    youth_representation_score = None
    if "age" in df.columns:
        with_age = df["age"].dropna()
        if len(with_age) > 0:
            youth_count = (with_age < 40).sum()
            youth_representation_score = round(float(youth_count / len(with_age) * 100), 2)

    # Independent Influence Index (0–100): independent candidate share (or vote share if available)
    independent_influence_index = None
    if "is_independent" in df.columns:
        ind_count = df["is_independent"].sum()
        independent_influence_index = round(float(ind_count / total * 100), 2) if total > 0 else None
    elif "party" in df.columns:
        ind_lower = df["party"].astype(str).str.strip().str.lower()
        ind_mask = ind_lower.isin(["स्वतन्त्र", "स्वतंत्र", "independent", "independent candidate", "independent (no party)"])
        independent_influence_index = round(float(ind_mask.sum() / total * 100), 2) if total > 0 else None

    # Female Representation % and Gender Parity Index
    female_representation_percentage = None
    gender_parity_index = None
    if "gender" in df.columns:
        gender_d = compute_gender_distribution(df)
        female_representation_percentage = gender_d.get("female_percentage")
        gender_parity_index = gender_d.get("gender_parity_index")

    summary_parts = [f"{total} candidates"]
    if avg_vote_share is not None:
        summary_parts.append(f"avg vote share {avg_vote_share}%")
    if avg_margin is not None:
        summary_parts.append(f"avg winner margin {avg_margin} pts")
    if education_index is not None:
        summary_parts.append(f"education index {education_index}")
    if local_pct is not None:
        summary_parts.append(f"local representation {local_pct}%")
    if symbol_coverage is not None:
        summary_parts.append(f"symbol diversity {symbol_coverage}%")
    if party_fragmentation_score is not None:
        summary_parts.append(f"party fragmentation {party_fragmentation_score}")
    if youth_representation_score is not None:
        summary_parts.append(f"youth representation {youth_representation_score}%")
    if independent_influence_index is not None:
        summary_parts.append(f"independent influence {independent_influence_index}")
    if female_representation_percentage is not None:
        summary_parts.append(f"female representation {female_representation_percentage}%")
    if gender_parity_index is not None:
        summary_parts.append(f"gender parity {gender_parity_index}")
    smart_voter_summary = ". ".join(summary_parts) + "."

    return {
        "candidate_count": total,
        "avg_vote_share": avg_vote_share,
        "avg_margin_winner": avg_margin,
        "education_index": education_index,
        "local_percentage": local_pct,
        "symbol_coverage": symbol_coverage,
        "winner_count": winner_count,
        "party_fragmentation_score": party_fragmentation_score,
        "youth_representation_score": youth_representation_score,
        "independent_influence_index": independent_influence_index,
        "female_representation_percentage": female_representation_percentage,
        "gender_parity_index": gender_parity_index,
        "smart_voter_summary": smart_voter_summary,
    }


def compute_gender_zero_districts(df: pd.DataFrame) -> Dict:
    """Districts with zero female candidates."""
    if "district" not in df.columns or "gender" not in df.columns:
        return {"districts": [], "count": 0}
    by_dist = df.groupby("district").apply(
        lambda g: (g["gender"].fillna("").astype(str).str.upper().isin(["F", "FEMALE"])).sum()
    )
    zero_female = by_dist[by_dist == 0].index.tolist()
    return {"districts": sorted(zero_female), "count": len(zero_female)}


def compute_top_female_concentration_districts(
    df: pd.DataFrame, top_n: int = 5
) -> Dict:
    """Top N districts by female candidate concentration (female %)."""
    if "district" not in df.columns or "gender" not in df.columns:
        return {"districts": []}
    rows = []
    for dist, g in df.groupby("district"):
        total = len(g)
        if total == 0:
            continue
        female_count = (g["gender"].fillna("").astype(str).str.upper().isin(["F", "FEMALE"])).sum()
        female_pct = round(float(female_count / total * 100), 1)
        province = g["province"].iloc[0] if "province" in g.columns else None
        rows.append({
            "district": str(dist),
            "province": str(province) if province else None,
            "female_percentage": female_pct,
            "total_candidates": int(total),
        })
    rows.sort(key=lambda x: x["female_percentage"], reverse=True)
    return {"districts": rows[:top_n]}


def compute_state_female_concentration(df: pd.DataFrame) -> Dict:
    """High and low provinces (states) by female candidate concentration."""
    if "province" not in df.columns or "gender" not in df.columns:
        return {"high": [], "low": []}
    rows = []
    for prov, g in df.groupby("province"):
        total = len(g)
        if total == 0:
            continue
        female_count = (g["gender"].fillna("").astype(str).str.upper().isin(["F", "FEMALE"])).sum()
        female_pct = round(float(female_count / total * 100), 1)
        rows.append({
            "province": str(prov),
            "female_percentage": female_pct,
            "candidate_count": int(total),
        })
    rows.sort(key=lambda x: x["female_percentage"], reverse=True)
    high = rows[:3] if len(rows) >= 3 else rows
    low = rows[-3:][::-1] if len(rows) >= 3 else rows[::-1]
    return {"high": high, "low": low}


def compute_geographic_indicators(df: pd.DataFrame) -> Dict:
    """Gender-zero districts, top 5 female-concentration districts, high/low state female concentration."""
    gender_zero = compute_gender_zero_districts(df)
    top_female = compute_top_female_concentration_districts(df, top_n=5)
    state_female = compute_state_female_concentration(df)
    return {
        "gender_zero_districts": gender_zero["districts"],
        "gender_zero_count": gender_zero["count"],
        "top_female_districts": top_female["districts"],
        "state_female_high": state_female["high"],
        "state_female_low": state_female["low"],
    }
