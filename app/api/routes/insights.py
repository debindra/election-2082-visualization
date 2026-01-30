"""
API routes for insight analysis.

This module exposes:
- A comprehensive `/insights` endpoint for longitudinal analytics
- Focused endpoints for specific insights needed by the UI:
  - Independent Wave (district-level independent strength)
  - District Competition Pressure
  - Party Saturation vs Reach
"""
from fastapi import APIRouter, HTTPException, Query

from app.data.loader import loader
from app.services.insight_service import compute_insights
from app.schemas.insight_response import (
    InsightResponse,
    InsightMetric,
    DistrictIndependentWaveResponse,
    DistrictCompetitionPressureResponse,
    PartySaturationResponse,
    AgeGapResponse,
    AgeGapMovementMetric,
    GenderGapResponse,
    YearInsightsResponse,
    AgeDemographicsResponse,
    AgeBandMetric,
    EducationProfileResponse,
    EducationLevelMetric,
    PartyVsAgeResponse,
    PartyAgeMetric,
    GenderDemographicsResponse,
    GenderDistributionMetric,
    PartyVsGenderResponse,
    PartyGenderMetric,
    BirthplaceVsContestResponse,
    SymbolRecognitionResponse,
    SymbolCountMetric,
    CompositeMetricsResponse,
    GeographicIndicatorsResponse,
    TopFemaleDistrictMetric,
    StateFemaleMetric,
)
from app.utils.metrics import (
    compute_independent_vote_share_by_district,
    compute_competition_pressure_by_district,
    compute_district_competition_intensity,
    compute_party_saturation,
    compute_age_gap_by_movement,
    compute_age_demographics,
    compute_education_profile,
    compute_party_vs_age,
    compute_gender_distribution,
    compute_party_vs_gender,
    compute_birthplace_vs_contest,
    compute_symbol_recognition,
    compute_composite_metrics,
    compute_geographic_indicators,
)

router = APIRouter(prefix="/insights", tags=["insights"])


@router.get("", response_model=InsightResponse)
async def get_insights(
    election_year: int = Query(..., ge=2000, le=2100, description="Election year"),
    compare_with: int = Query(None, ge=2000, le=2100, description="Year to compare with"),
):
    """
    Get comprehensive insights for an election year.
    
    Computes all longitudinal insights including:
    - Independent candidate structural shift
    - Party retrenchment vs expansion
    - Candidate age trends
    - Urban political fragmentation
    - Education profile evolution
    - Local vs outsider candidate trend
    - Party stability vs volatility
    - Candidate density vs voter choice
    - Symbol saturation
    - Political churn index
    """
    try:
        insights_data = compute_insights(election_year, compare_with)
        
        # Convert to response format
        insights = {}
        for key, insight in insights_data["insights"].items():
            insights[key] = InsightMetric(
                name=insight["name"],
                value=insight["value"],
                description=insight["description"],
                trend=insight.get("trend"),
            )
        
        return InsightResponse(
            election_year=insights_data["election_year"],
            compare_with=insights_data.get("compare_with"),
            insights=insights,
            breakdown={k: v.get("details", {}) for k, v in insights_data["insights"].items()},
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute insights: {str(e)}")


@router.get(
    "/independent-wave",
    response_model=DistrictIndependentWaveResponse,
    summary="Independent Wave Insight (district-level)",
)
async def get_independent_wave_insight(
    election_year: int = Query(..., ge=2000, le=2100, description="Election year"),
):
    """
    Independent Wave Insight: district-level independent strength.

    Computes independent vote share (or candidate share where vote data
    is missing) per district for a given election year.
    """
    try:
        df, _ = loader.load_election(election_year)
        metrics = compute_independent_vote_share_by_district(df)

        return DistrictIndependentWaveResponse(
            election_year=election_year,
            method=metrics.get("method", "unknown"),
            districts=metrics.get("districts", []),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute independent wave insight: {str(e)}"
        )


@router.get(
    "/competition-pressure",
    response_model=DistrictCompetitionPressureResponse,
    summary="District Competition Pressure",
)
async def get_competition_pressure_insight(
    election_year: int = Query(..., ge=2000, le=2100, description="Election year"),
):
    """
    District Competition Pressure Insight.

    For each district, computes the average vote-share gap between the
    top 2–3 candidates, aggregated from constituency-level results.
    """
    try:
        df, _ = loader.load_election(election_year)
        metrics = compute_competition_pressure_by_district(df)
        intensity = compute_district_competition_intensity(df, top_n=15)

        return DistrictCompetitionPressureResponse(
            election_year=election_year,
            districts=metrics.get("districts", []),
            top_districts_by_candidates=intensity.get("top_districts") or None,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute competition pressure insight: {str(e)}"
        )


@router.get(
    "/party-saturation",
    response_model=PartySaturationResponse,
    summary="Party Saturation vs Reach",
)
async def get_party_saturation_insight(
    election_year: int = Query(..., ge=2000, le=2100, description="Election year"),
):
    """
    Party Saturation vs Reach Insight.

    For each party, returns candidate counts, seats contested, seats won,
    and a simple win rate for the given election year.
    """
    try:
        df, _ = loader.load_election(election_year)
        metrics = compute_party_saturation(df)

        return PartySaturationResponse(
            election_year=election_year,
            parties=metrics.get("parties", []),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute party saturation insight: {str(e)}"
        )


@router.get(
    "/age-gap",
    response_model=AgeGapResponse,
    summary="Age Gap Between Political Movements",
)
async def get_age_gap_insight(
    election_year: int = Query(..., ge=2000, le=2100, description="Election year"),
):
    """
    Age Gap Between Political Movements.

    Average age difference between:
    - Top 3 legacy parties (by candidate count)
    - New/alternative parties (all other non-independent parties)
    - Independents

    Power insight: "Youth participation is rising — but mostly outside traditional parties."
    """
    try:
        df, _ = loader.load_election(election_year)
        metrics = compute_age_gap_by_movement(df)

        def to_metric(d: dict, parties: list = None):
            return AgeGapMovementMetric(
                average_age=d.get("average_age"),
                candidate_count=d.get("candidate_count", 0),
                parties=parties if parties is not None else d.get("parties"),
            )

        return AgeGapResponse(
            election_year=election_year,
            top3_legacy=to_metric(metrics["top3_legacy"], metrics["top3_legacy"].get("parties")),
            new_alternative=to_metric(metrics["new_alternative"]),
            independents=to_metric(metrics["independents"]),
            power_insight=metrics.get("power_insight", "Youth participation is rising — but mostly outside traditional parties."),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to compute age gap insight: {str(e)}"
        )


@router.get(
    "/gender-gap",
    response_model=GenderGapResponse,
    summary="Gender Gap Insight",
)
async def get_gender_gap_insight(
    election_year: int = Query(..., ge=2000, le=2100, description="Election year"),
):
    """
    Gender Gap Insight: female candidate representation and gender parity.

    Returns female percentage, gender parity index, and distribution by gender.
    Power insight: highlights progress or gaps in gender representation.
    """
    try:
        df, _ = loader.load_election(election_year)
        metrics = compute_gender_distribution(df)
        return GenderGapResponse(
            election_year=election_year,
            female_percentage=metrics.get("female_percentage"),
            gender_parity_index=metrics.get("gender_parity_index"),
            distribution=[
                GenderDistributionMetric(gender=d["gender"], count=d["count"], percentage=d["percentage"])
                for d in metrics.get("distribution", [])
            ],
            power_insight=metrics.get("power_insight", ""),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute gender gap insight: {str(e)}")


def _match_col_or_en(df, main_col: str, en_col: str, value: str, extra_cols=None):
    """Boolean series: row matches value in main_col, en_col, or extra_cols."""
    m = df[main_col].astype(str).str.contains(value, case=False, na=False)
    if en_col in df.columns:
        m = m | df[en_col].fillna("").astype(str).str.contains(value, case=False)
    for col in extra_cols or []:
        if col in df.columns:
            m = m | df[col].fillna("").astype(str).str.contains(value, case=False)
    return m


@router.get(
    "/year-insights",
    response_model=YearInsightsResponse,
    summary="Year insights (filtered by party / province / district / gender)",
)
async def get_year_insights(
    election_year: int = Query(..., ge=2000, le=2100, description="Election year"),
    province: str = Query(None, description="Filter by province (state)"),
    district: str = Query(None, description="Filter by district"),
    party: str = Query(None, description="Filter by party"),
    gender: str = Query(None, description="Filter by gender (M/F/Other)"),
):
    """
    Individual election year insights, filterable by party, state (province), district, and gender.

    Returns seven insight blocks:
    1. Age Demographics of Candidates
    2. Gender Demographics (when gender data available)
    3. Education Profile Insight
    4. Party vs Age Trend (Power Insight)
    5. Party vs Gender (Power Insight)
    6. Birthplace vs Contest District (Local Representation)
    7. Symbol Recognition Analysis (UX Insight)
    8. High-Value Composite Metrics (For Smart Voters)
    """
    try:
        df, _ = loader.load_election(election_year)
        filtered = df.copy()
        if province:
            filtered = filtered[_match_col_or_en(filtered, "province", "province_en", province, ["province_np"])]
        if district:
            filtered = filtered[_match_col_or_en(filtered, "district", "district_en", district)]
        if party:
            filtered = filtered[_match_col_or_en(filtered, "party", "party_en", party)]
        if gender and "gender" in filtered.columns:
            g_val = str(gender).strip().upper()
            filtered = filtered[filtered["gender"].fillna("").astype(str).str.upper() == g_val]

        age_d = compute_age_demographics(filtered)
        gender_d = compute_gender_distribution(filtered)
        edu_d = compute_education_profile(filtered)
        party_age_d = compute_party_vs_age(filtered)
        party_gender_d = compute_party_vs_gender(filtered)
        local_d = compute_birthplace_vs_contest(filtered)
        symbol_d = compute_symbol_recognition(filtered)
        composite_d = compute_composite_metrics(filtered)
        geo_d = compute_geographic_indicators(filtered)

        return YearInsightsResponse(
            election_year=election_year,
            province=province or None,
            district=district or None,
            party=party or None,
            gender=gender or None,
            age_demographics=AgeDemographicsResponse(
                bands=[AgeBandMetric(band=b["band"], count=b["count"], percentage=b["percentage"]) for b in age_d["bands"]],
                average_age=age_d.get("average_age"),
                median_age=age_d.get("median_age"),
                total_with_age=age_d.get("total_with_age", 0),
            ),
            education_profile=EducationProfileResponse(
                distribution=[
                    EducationLevelMetric(level=d["level"], count=d["count"], percentage=d["percentage"])
                    for d in edu_d["distribution"]
                ],
                average_index=edu_d.get("average_index"),
                total_with_education=edu_d.get("total_with_education", 0),
            ),
            party_vs_age=PartyVsAgeResponse(
                parties=[
                    PartyAgeMetric(party=p["party"], average_age=p.get("average_age"), candidate_count=p["candidate_count"])
                    for p in party_age_d["parties"]
                ],
                power_insight=party_age_d.get("power_insight", ""),
            ),
            gender_demographics=GenderDemographicsResponse(
                distribution=[
                    GenderDistributionMetric(gender=d["gender"], count=d["count"], percentage=d["percentage"])
                    for d in gender_d["distribution"]
                ],
                female_percentage=gender_d.get("female_percentage"),
                gender_parity_index=gender_d.get("gender_parity_index"),
                total_with_gender=gender_d.get("total_with_gender", 0),
                power_insight=gender_d.get("power_insight", ""),
            ) if gender_d.get("total_with_gender", 0) > 0 else None,
            party_vs_gender=PartyVsGenderResponse(
                parties=[
                    PartyGenderMetric(
                        party=p["party"],
                        female_count=p["female_count"],
                        female_percentage=p.get("female_percentage"),
                        candidate_count=p["candidate_count"],
                    )
                    for p in party_gender_d["parties"]
                ],
                power_insight=party_gender_d.get("power_insight", ""),
            ) if party_gender_d.get("parties") else None,
            birthplace_vs_contest=BirthplaceVsContestResponse(
                local_count=local_d.get("local_count", 0),
                outsider_count=local_d.get("outsider_count", 0),
                local_percentage=local_d.get("local_percentage"),
                unknown_count=local_d.get("unknown_count", 0),
                total_with_birthplace=local_d.get("total_with_birthplace", 0),
            ),
            symbol_recognition=SymbolRecognitionResponse(
                symbols=[
                    SymbolCountMetric(
                        symbol=s["symbol"],
                        candidate_count=s["candidate_count"],
                        percentage=s["percentage"],
                        party_name=s.get("party_name"),
                    )
                    for s in symbol_d["symbols"]
                ],
                unique_symbols=symbol_d.get("unique_symbols", 0),
                saturation_index=symbol_d.get("saturation_index"),
                ux_insight=symbol_d.get("ux_insight", ""),
            ),
            composite_metrics=CompositeMetricsResponse(
                candidate_count=composite_d.get("candidate_count", 0),
                avg_vote_share=composite_d.get("avg_vote_share"),
                avg_margin_winner=composite_d.get("avg_margin_winner"),
                education_index=composite_d.get("education_index"),
                local_percentage=composite_d.get("local_percentage"),
                symbol_coverage=composite_d.get("symbol_coverage"),
                winner_count=composite_d.get("winner_count"),
                party_fragmentation_score=composite_d.get("party_fragmentation_score"),
                youth_representation_score=composite_d.get("youth_representation_score"),
                independent_influence_index=composite_d.get("independent_influence_index"),
                female_representation_percentage=composite_d.get("female_representation_percentage"),
                gender_parity_index=composite_d.get("gender_parity_index"),
                smart_voter_summary=composite_d.get("smart_voter_summary", ""),
            ),
            geographic_indicators=GeographicIndicatorsResponse(
                gender_zero_districts=geo_d.get("gender_zero_districts", []),
                gender_zero_count=geo_d.get("gender_zero_count", 0),
                top_female_districts=[
                    TopFemaleDistrictMetric(
                        district=d["district"],
                        province=d.get("province"),
                        female_percentage=d["female_percentage"],
                        total_candidates=d["total_candidates"],
                    )
                    for d in geo_d.get("top_female_districts", [])
                ],
                state_female_high=[
                    StateFemaleMetric(
                        province=s["province"],
                        female_percentage=s["female_percentage"],
                        candidate_count=s["candidate_count"],
                    )
                    for s in geo_d.get("state_female_high", [])
                ],
                state_female_low=[
                    StateFemaleMetric(
                        province=s["province"],
                        female_percentage=s["female_percentage"],
                        candidate_count=s["candidate_count"],
                    )
                    for s in geo_d.get("state_female_low", [])
                ],
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compute year insights: {str(e)}")
