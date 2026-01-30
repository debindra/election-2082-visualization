"""
Pydantic schemas for insight responses.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field


class InsightMetric(BaseModel):
    """Single insight metric."""
    name: str = Field(..., description="Metric name")
    value: Any = Field(..., description="Metric value")
    description: Optional[str] = Field(None, description="Metric description")
    trend: Optional[str] = Field(None, description="Trend direction")


class InsightResponse(BaseModel):
    """Insight analysis response."""
    election_year: int = Field(..., description="Election year")
    compare_with: Optional[int] = Field(None, description="Comparison year")
    insights: Dict[str, InsightMetric] = Field(..., description="Insights by category")
    breakdown: Optional[Dict[str, Any]] = Field(None, description="Detailed breakdown")


class DistrictIndependentWaveMetric(BaseModel):
    """Independent candidate strength for a single district."""
    district: str = Field(..., description="District name")
    independent_vote_share: Optional[float] = Field(
        None, description="Independent vote share in district (0-100, if votes available)"
    )
    independent_candidate_share: Optional[float] = Field(
        None, description="Share of independent candidates in district (0-100)"
    )
    total_votes: Optional[float] = Field(None, description="Total votes counted in district")
    total_candidates: int = Field(..., description="Total candidates in district")


class DistrictIndependentWaveResponse(BaseModel):
    """Response for independent wave insight by district."""
    election_year: int = Field(..., description="Election year")
    method: str = Field(
        ...,
        description="Computation method: 'votes' (vote-based share) or 'candidates' (candidate share only)",
    )
    districts: List[DistrictIndependentWaveMetric] = Field(
        ..., description="Independent strength per district"
    )


class DistrictCompetitionMetric(BaseModel):
    """Competition pressure metrics for a single district."""
    district: str = Field(..., description="District name")
    avg_margin_top2: Optional[float] = Field(
        None, description="Average vote-share gap between top 2 candidates (percentage points)"
    )
    avg_margin_top3: Optional[float] = Field(
        None, description="Average vote-share gap between winner and 3rd place (percentage points)"
    )


class DistrictPartyCount(BaseModel):
    """Candidate count for a party in a district."""
    party: str = Field(..., description="Party name")
    count: int = Field(..., description="Number of candidates")


class DistrictIntensityMetric(BaseModel):
    """District-level competition intensity: candidates per district with party breakdown."""
    district: str = Field(..., description="District name")
    total_candidates: int = Field(..., description="Total number of candidates in district")
    by_party: List[DistrictPartyCount] = Field(
        default_factory=list,
        description="Candidate count per party (for stacked chart)",
    )


class DistrictCompetitionPressureResponse(BaseModel):
    """Response for district competition pressure insight."""
    election_year: int = Field(..., description="Election year")
    districts: List[DistrictCompetitionMetric] = Field(
        ..., description="Competition pressure metrics per district"
    )
    top_districts_by_candidates: Optional[List[DistrictIntensityMetric]] = Field(
        None,
        description="Top districts by number of candidates, with breakdown by party (competition intensity)",
    )


class PartySaturationMetric(BaseModel):
    """Party saturation vs reach metrics for a single party."""
    party: str = Field(..., description="Party name")
    candidates: int = Field(..., description="Total number of candidates for this party")
    seats_contested: Optional[int] = Field(
        None, description="Number of unique constituencies this party contested"
    )
    seats_won: Optional[int] = Field(
        None, description="Number of constituencies this party won (if winner data is available)"
    )
    win_rate: Optional[float] = Field(
        None, description="Win rate in contested constituencies (0-100, if computable)"
    )


class PartySaturationResponse(BaseModel):
    """Response for party saturation vs reach insight."""
    election_year: int = Field(..., description="Election year")
    parties: List[PartySaturationMetric] = Field(
        ..., description="Party saturation metrics"
    )


class AgeGapMovementMetric(BaseModel):
    """Average age and count for a political movement (legacy / new / independents)."""
    average_age: Optional[float] = Field(None, description="Average candidate age")
    candidate_count: int = Field(..., description="Number of candidates")
    parties: Optional[List[str]] = Field(None, description="Party names (only for top3_legacy)")


class AgeGapResponse(BaseModel):
    """Response for Age Gap Between Political Movements insight."""
    election_year: int = Field(..., description="Election year")
    top3_legacy: AgeGapMovementMetric = Field(
        ..., description="Top 3 legacy parties by candidate count: average age and count"
    )
    new_alternative: AgeGapMovementMetric = Field(
        ..., description="New/alternative parties (non-top-3, non-independent): average age and count"
    )
    independents: AgeGapMovementMetric = Field(
        ..., description="Independent candidates: average age and count"
    )
    power_insight: str = Field(
        ...,
        description="Power insight: Youth participation outside traditional parties",
    )


# --- Year insights (filtered by party / province / district) ---


class AgeBandMetric(BaseModel):
    """Age band count and percentage."""
    band: str = Field(..., description="Age band label (e.g. 25-34)")
    count: int = Field(..., description="Candidate count in band")
    percentage: float = Field(..., description="Percentage of candidates with age in this band")


class AgeDemographicsResponse(BaseModel):
    """Age demographics of candidates."""
    bands: List[AgeBandMetric] = Field(..., description="Count and share per age band")
    average_age: Optional[float] = Field(None, description="Average candidate age")
    median_age: Optional[float] = Field(None, description="Median candidate age")
    total_with_age: int = Field(..., description="Candidates with age data")


class EducationLevelMetric(BaseModel):
    """Education level count and percentage."""
    level: str = Field(..., description="Education level label")
    count: int = Field(..., description="Candidate count")
    percentage: float = Field(..., description="Percentage")


class EducationProfileResponse(BaseModel):
    """Education profile insight."""
    distribution: List[EducationLevelMetric] = Field(..., description="Distribution by level")
    average_index: Optional[float] = Field(None, description="Weighted education index")
    total_with_education: int = Field(..., description="Candidates with education data")


class PartyAgeMetric(BaseModel):
    """Party average age and count."""
    party: str = Field(..., description="Party name")
    average_age: Optional[float] = Field(None, description="Average candidate age")
    candidate_count: int = Field(..., description="Candidate count")


class PartyVsAgeResponse(BaseModel):
    """Party vs age trend (power insight)."""
    parties: List[PartyAgeMetric] = Field(..., description="Average age per party")
    power_insight: str = Field(..., description="Power insight text")


class GenderDistributionMetric(BaseModel):
    """Gender count and percentage."""
    gender: str = Field(..., description="Gender code (M/F/Other)")
    count: int = Field(..., description="Candidate count")
    percentage: float = Field(..., description="Percentage of candidates with gender data")


class GenderDemographicsResponse(BaseModel):
    """Gender demographics of candidates."""
    distribution: List[GenderDistributionMetric] = Field(..., description="Count and share per gender")
    female_percentage: Optional[float] = Field(None, description="Female candidate percentage")
    gender_parity_index: Optional[float] = Field(None, description="Gender parity index 0-1")
    total_with_gender: int = Field(..., description="Candidates with gender data")
    power_insight: str = Field(..., description="Power insight text")


class PartyGenderMetric(BaseModel):
    """Party female share and count."""
    party: str = Field(..., description="Party name")
    female_count: int = Field(..., description="Female candidate count")
    female_percentage: Optional[float] = Field(None, description="Female candidate percentage")
    candidate_count: int = Field(..., description="Total candidate count")


class PartyVsGenderResponse(BaseModel):
    """Party vs gender (power insight)."""
    parties: List[PartyGenderMetric] = Field(..., description="Female share per party")
    power_insight: str = Field(..., description="Power insight text")


class GenderGapResponse(BaseModel):
    """Response for Gender Gap insight."""
    election_year: int = Field(..., description="Election year")
    female_percentage: Optional[float] = Field(None, description="Female candidate percentage")
    gender_parity_index: Optional[float] = Field(None, description="Gender parity index 0-1")
    distribution: List[GenderDistributionMetric] = Field(
        default_factory=list,
        description="Gender distribution (M/F/Other)",
    )
    power_insight: str = Field(..., description="Power insight text")


class BirthplaceVsContestResponse(BaseModel):
    """Birthplace vs contest district (local representation)."""
    local_count: int = Field(..., description="Candidates contesting in birth district")
    outsider_count: int = Field(..., description="Candidates contesting outside birth district")
    local_percentage: Optional[float] = Field(None, description="Percentage local")
    unknown_count: int = Field(..., description="Candidates without birth place data")
    total_with_birthplace: int = Field(..., description="Candidates with birth place data")


class SymbolCountMetric(BaseModel):
    """Symbol candidate count and share."""
    symbol: str = Field(..., description="Election symbol label")
    candidate_count: int = Field(..., description="Candidate count")
    percentage: float = Field(..., description="Percentage of candidates")
    party_name: Optional[str] = Field(None, description="Party name (for tooltip/hover)")


class SymbolRecognitionResponse(BaseModel):
    """Symbol recognition analysis (UX insight)."""
    symbols: List[SymbolCountMetric] = Field(..., description="Top symbols by count")
    unique_symbols: int = Field(..., description="Total unique symbols")
    saturation_index: Optional[float] = Field(None, description="Unique symbols per 100 candidates")
    ux_insight: str = Field(..., description="UX insight text")


class CompositeMetricsResponse(BaseModel):
    """High-value composite metrics for smart voters."""
    candidate_count: int = Field(..., description="Total candidates in selection")
    avg_vote_share: Optional[float] = Field(None, description="Average vote share %")
    avg_margin_winner: Optional[float] = Field(None, description="Average winner margin (pts)")
    education_index: Optional[float] = Field(None, description="Education index")
    local_percentage: Optional[float] = Field(None, description="Local representation %")
    symbol_coverage: Optional[float] = Field(None, description="Symbol diversity %")
    winner_count: Optional[int] = Field(None, description="Number of winners")
    party_fragmentation_score: Optional[float] = Field(
        None, description="Party Fragmentation Score (0–100, Herfindahl-based)"
    )
    youth_representation_score: Optional[float] = Field(
        None, description="Youth Representation Score (% of candidates under 40)"
    )
    independent_influence_index: Optional[float] = Field(
        None, description="Independent Influence Index (independent candidate share 0–100)"
    )
    female_representation_percentage: Optional[float] = Field(
        None, description="Female candidate percentage"
    )
    gender_parity_index: Optional[float] = Field(
        None, description="Gender parity index 0–1 (1 = perfect parity)"
    )
    smart_voter_summary: str = Field(..., description="Summary for smart voters")


class TopFemaleDistrictMetric(BaseModel):
    """District with high female candidate concentration."""
    district: str = Field(..., description="District name")
    province: Optional[str] = Field(None, description="Province name")
    female_percentage: float = Field(..., description="Female candidate percentage")
    total_candidates: int = Field(..., description="Total candidates in district")


class StateFemaleMetric(BaseModel):
    """Province (state) female concentration."""
    province: str = Field(..., description="Province/state name")
    female_percentage: float = Field(..., description="Female candidate percentage")
    candidate_count: int = Field(..., description="Candidate count")


class GeographicIndicatorsResponse(BaseModel):
    """Geographic indicators: gender-zero districts, top female districts, high/low state female concentration."""
    gender_zero_districts: List[str] = Field(
        default_factory=list,
        description="Districts with zero female candidates",
    )
    gender_zero_count: int = Field(..., description="Count of gender-zero districts")
    top_female_districts: List[TopFemaleDistrictMetric] = Field(
        default_factory=list,
        description="Top 5 districts by female candidate concentration",
    )
    state_female_high: List[StateFemaleMetric] = Field(
        default_factory=list,
        description="Provinces with highest female concentration",
    )
    state_female_low: List[StateFemaleMetric] = Field(
        default_factory=list,
        description="Provinces with lowest female concentration",
    )


class YearInsightsResponse(BaseModel):
    """Combined response for year insights (filtered by party / province / district)."""
    election_year: int = Field(..., description="Election year")
    province: Optional[str] = Field(None, description="Filter: province")
    district: Optional[str] = Field(None, description="Filter: district")
    party: Optional[str] = Field(None, description="Filter: party")
    gender: Optional[str] = Field(None, description="Filter: gender")
    age_demographics: AgeDemographicsResponse = Field(..., description="Age demographics")
    gender_demographics: Optional[GenderDemographicsResponse] = Field(
        None, description="Gender demographics"
    )
    education_profile: EducationProfileResponse = Field(..., description="Education profile")
    party_vs_age: PartyVsAgeResponse = Field(..., description="Party vs age trend")
    party_vs_gender: Optional[PartyVsGenderResponse] = Field(
        None, description="Party vs gender representation"
    )
    birthplace_vs_contest: BirthplaceVsContestResponse = Field(..., description="Local representation")
    symbol_recognition: SymbolRecognitionResponse = Field(..., description="Symbol recognition")
    composite_metrics: CompositeMetricsResponse = Field(..., description="Composite metrics for smart voters")
    geographic_indicators: Optional[GeographicIndicatorsResponse] = Field(
        None, description="Geographic indicators: gender-zero districts, high-concentration, state summary"
    )
