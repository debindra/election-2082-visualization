# Analytics modules for longitudinal insights

from app.analytics.independent_shift import analyze_independent_shift
from app.analytics.party_retrenchment import analyze_party_retrenchment
from app.analytics.age_trend import analyze_age_trends
from app.analytics.urban_fragmentation import analyze_urban_fragmentation
from app.analytics.education_evolution import analyze_education_evolution
from app.analytics.local_vs_outsider import analyze_local_vs_outsider
from app.analytics.party_volatility import analyze_party_volatility
from app.analytics.candidate_density import analyze_candidate_density
from app.analytics.symbol_saturation import analyze_symbol_saturation
from app.analytics.political_churn import analyze_political_churn

__all__ = [
    "analyze_independent_shift",
    "analyze_party_retrenchment",
    "analyze_age_trends",
    "analyze_urban_fragmentation",
    "analyze_education_evolution",
    "analyze_local_vs_outsider",
    "analyze_party_volatility",
    "analyze_candidate_density",
    "analyze_symbol_saturation",
    "analyze_political_churn",
]
