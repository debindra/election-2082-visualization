"""
Service for comparing candidates by ID.
"""
from typing import Dict, List, Optional
import logging

import pandas as pd

from app.data.loader import loader

logger = logging.getLogger(__name__)


def _load_all_relevant_elections(election_year: Optional[int]) -> Dict[int, pd.DataFrame]:
    """
    Load election DataFrames needed for comparison.

    Returns a mapping of election_year -> DataFrame.
    """
    elections: Dict[int, pd.DataFrame] = {}

    if election_year:
        try:
            df, _ = loader.load_election(election_year)
            elections[int(election_year)] = df
        except Exception as e:
            logger.error(f"Failed to load election {election_year}: {e}")
    else:
        for year in loader.list_available_elections():
            try:
                df, _ = loader.load_election(year)
                elections[int(year)] = df
            except Exception as e:
                logger.warning(f"Failed to load election {year}: {e}")

    return elections


def _attach_context_metrics(
    candidates: Dict[str, Dict],
    elections: Dict[int, pd.DataFrame],
) -> None:
    """
    Enrich candidate dicts in-place with contextual metrics:
    - vote_share_in_race
    - party_strength_in_district
    - party_incumbent_in_constituency (where previous election exists)
    """
    # Pre-compute previous election mapping per year (if sequential years exist)
    sorted_years = sorted(elections.keys())
    prev_year_for = {y: sorted_years[i - 1] for i, y in enumerate(sorted_years) if i > 0}

    for cand in candidates.values():
        year = cand.get("election_year")
        if year is None:
            # If not explicitly set, try to infer from a common column
            year = cand.get("election_year") or cand.get("year")
        if year is None:
            continue

        year = int(year)
        df = elections.get(year)
        if df is None:
            continue

        district = cand.get("district")
        constituency = cand.get("constituency")
        party = cand.get("party")
        votes_received = cand.get("votes_received")

        # Vote share in race (within same district+constituency)
        if (
            district
            and constituency
            and "votes_received" in df.columns
            and df["votes_received"].notna().any()
            and votes_received is not None
        ):
            race_df = df[
                (df["district"].astype(str) == str(district))
                & (df["constituency"].astype(str) == str(constituency))
            ]
            total_votes = float(race_df["votes_received"].fillna(0).sum())
            if total_votes > 0:
                cand["vote_share_in_race"] = round(float(votes_received) / total_votes * 100.0, 2)

        # Party strength in district (share of votes captured by this party)
        if (
            district
            and party
            and "votes_received" in df.columns
            and df["votes_received"].notna().any()
        ):
            dist_df = df[df["district"].astype(str) == str(district)]
            total_votes_dist = float(dist_df["votes_received"].fillna(0).sum())
            if total_votes_dist > 0:
                party_votes = float(
                    dist_df[dist_df["party"].astype(str) == str(party)]["votes_received"]
                    .fillna(0)
                    .sum()
                )
                cand["party_strength_in_district"] = round(
                    party_votes / total_votes_dist * 100.0, 2
                )

        # Party incumbent in constituency (previous election winner comparison)
        prev_year = prev_year_for.get(year)
        if prev_year and district and constituency and party:
            prev_df = elections.get(prev_year)
            if prev_df is not None and "is_winner" in prev_df.columns:
                prev_race = prev_df[
                    (prev_df["district"].astype(str) == str(district))
                    & (prev_df["constituency"].astype(str) == str(constituency))
                    & (prev_df["is_winner"] == True)
                ]
                if not prev_race.empty:
                    prev_party = prev_race.iloc[0].get("party")
                    if prev_party is not None:
                        cand["party_incumbent_in_constituency"] = str(prev_party) == str(party)


def compare_candidates(
    candidate_ids: List[str],
    election_year: Optional[int] = None,
) -> Dict:
    """
    Compare candidates by their IDs.
    
    Args:
        candidate_ids: List of candidate IDs to compare
        election_year: Specific election year (optional, searches all if None)
        
    Returns:
        Dictionary with candidate comparison data
    """
    # Load relevant elections once
    elections = _load_all_relevant_elections(election_year)

    candidates: Dict[str, Dict] = {}

    for year, df in elections.items():
        try:
            for candidate_id in candidate_ids:
                if candidate_id in candidates:
                    continue
                subset = df[df["candidate_id"].astype(str) == str(candidate_id)]
                if not subset.empty:
                    row = subset.iloc[0].to_dict()
                    # Ensure election_year is present for downstream context metrics
                    row.setdefault("election_year", year)
                    candidates[candidate_id] = row
        except Exception as e:
            logger.warning(f"Failed to search candidates in election {year}: {e}")
            continue

    # Attach contextual metrics per candidate
    if candidates:
        _attach_context_metrics(candidates, elections)

    # Compute comparison metrics
    comparison_metrics: Dict[str, Dict] = {}

    if len(candidates) > 1:
        # Age comparison
        ages = [c.get("age") for c in candidates.values() if c.get("age") is not None]
        if ages:
            comparison_metrics["age_range"] = {
                "min": min(ages),
                "max": max(ages),
                "average": sum(ages) / len(ages),
            }

        # Party distribution
        parties = [c.get("party") for c in candidates.values() if c.get("party")]
        if parties:
            from collections import Counter

            comparison_metrics["party_distribution"] = dict(Counter(parties))

        # Independent count
        independent_count = sum(1 for c in candidates.values() if c.get("is_independent"))
        comparison_metrics["independent_count"] = independent_count

        # Vote share range (where available)
        vote_shares = [
            c.get("vote_share_in_race")
            for c in candidates.values()
            if c.get("vote_share_in_race") is not None
        ]
        if vote_shares:
            comparison_metrics["vote_share_range"] = {
                "min": min(vote_shares),
                "max": max(vote_shares),
                "average": sum(vote_shares) / len(vote_shares),
            }

        # Party strength in district range
        party_strengths = [
            c.get("party_strength_in_district")
            for c in candidates.values()
            if c.get("party_strength_in_district") is not None
        ]
        if party_strengths:
            comparison_metrics["party_strength_in_district_range"] = {
                "min": min(party_strengths),
                "max": max(party_strengths),
                "average": sum(party_strengths) / len(party_strengths),
            }

        # Gender distribution
        genders = [c.get("gender") for c in candidates.values() if c.get("gender")]
        if genders:
            from collections import Counter
            comparison_metrics["gender_distribution"] = dict(Counter(genders))

    return {
        "candidates": candidates,
        "comparison_metrics": comparison_metrics,
    }


def search_candidates(
    query: str,
    limit: int = 5,
    election_year: Optional[int] = None,
) -> List[Dict]:
    """
    Search candidates by ID or name; return top `limit` matches for autocomplete.

    Matches against:
    - candidate_id
    - Candidate Full Name (default, typically Nepali)
    - Candidate Full Name In English (when column present)
    - Other _en / _np fields (district, party, province, etc.) when present.

    Args:
        query: Search string (matched against names, ID, and optional _en fields).
        limit: Max results to return (default 5).
        election_year: Optional year to restrict search.

    Returns:
        List of dicts with candidate_id, candidate_name, party, election_year, and _en fields when present.
    """
    if not query or not str(query).strip():
        return []

    q = str(query).strip().lower()
    results: List[Dict] = []
    seen: set = set()  # (candidate_id, election_year) to avoid duplicates

    years = [election_year] if election_year else loader.list_available_elections()
    for year in years:
        try:
            df, _ = loader.load_election(year)
        except Exception as e:
            logger.warning(f"Failed to load election {year}: {e}")
            continue

        en_cols = {c for c in ("candidate_name_en", "district_en", "birth_place_en", "party_en", "province_en", "province_np") if c in df.columns}
        has_name_en = "candidate_name_en" in df.columns

        def _str(v):
            if v is None or (isinstance(v, float) and pd.isna(v)):
                return ""
            s = str(v).strip()
            return s if s.lower() not in ("nan", "none", "") else ""

        for _, row in df.iterrows():
            if len(results) >= limit:
                return results

            cid = str(row.get("candidate_id", "")).strip()
            key = (cid, year)
            if key in seen:
                continue
            seen.add(key)

            # Search both: (1) Candidate Full Name [default], (2) Candidate Full Name In English
            name_default = _str(row.get("candidate_name"))
            name_english = _str(row.get("candidate_name_en")) if has_name_en else ""
            searchable = [cid.lower()]
            if name_default:
                searchable.append(name_default.lower())
            if name_english:
                searchable.append(name_english.lower())
            for col in en_cols:
                if col == "candidate_name_en":
                    continue
                val = _str(row.get(col))
                if val:
                    searchable.append(val.lower())

            # Match: full phrase (substring or startswith) OR all query words appear in any searchable
            words = [w for w in q.split() if w]
            match = any(q in s or s.startswith(q) for s in searchable) or (
                len(words) > 0 and all(any(w in s for s in searchable) for w in words)
            )

            if not match:
                continue

            party_val = row.get("party")
            if party_val is None or (isinstance(party_val, float) and pd.isna(party_val)):
                party_val = None
            elif isinstance(party_val, str) and party_val.strip().lower() in ("nan", "none", ""):
                party_val = None
            out = {
                "candidate_id": cid,
                "candidate_name": name_default or None,
                "party": party_val or None,
                "election_year": int(year) if year else None,
            }
            if "candidate_name_en" in en_cols:
                v = _str(row.get("candidate_name_en"))
                if v:
                    out["candidate_name_en"] = v
            if "party_en" in en_cols:
                v = _str(row.get("party_en"))
                if v:
                    out["party_en"] = v
            if "district_en" in en_cols:
                v = _str(row.get("district_en"))
                if v:
                    out["district_en"] = v
            if "province_en" in en_cols:
                v = _str(row.get("province_en"))
                if v:
                    out["province_en"] = v
            if "province_np" in en_cols:
                v = _str(row.get("province_np"))
                if v:
                    out["province_np"] = v
            if "birth_place_en" in en_cols:
                v = _str(row.get("birth_place_en"))
                if v:
                    out["birth_place_en"] = v
            results.append(out)

    return results[:limit]
