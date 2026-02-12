"""
Analytics Service using Pandas

Handles exact lookups, counts, aggregations, and statistics.
"""
import logging
from typing import Dict, Any, List, Optional
import pandas as pd
from rapidfuzz import process, fuzz

from config.settings import settings

logger = logging.getLogger(__name__)


class ElectionAnalyticsService:
    """
    Service for analytics operations on election data.
    
    Uses pandas for efficient data processing and analysis.
    """
    
    def __init__(self, 
                 candidates_csv: str = None,
                 voting_centers_csv: str = None):
        """
        Initialize analytics service.
        
        Args:
            candidates_csv: Path to candidates CSV file
            voting_centers_csv: Path to voting centers CSV file
        """
        self.candidates_csv = candidates_csv or settings.candidates_csv
        self.voting_centers_csv = voting_centers_csv or settings.voting_centers_csv
        
        # Load data
        logger.info(f"Loading candidates from {self.candidates_csv}")
        self.candidates_df = pd.read_csv(self.candidates_csv)
        logger.info(f"Loaded {len(self.candidates_df)} candidates")
        
        logger.info(f"Loading voting centers from {self.voting_centers_csv}")
        self.voting_centers_df = pd.read_csv(self.voting_centers_csv)
        logger.info(f"Loaded {len(self.voting_centers_df)} voting centers")
        
        # Clean numeric columns
        self._clean_dataframes()
        
        logger.info("Analytics service initialized")
    
    def _clean_dataframes(self):
        """Clean and standardize dataframes."""
        # Ensure numeric columns are numeric
        numeric_cols_candidates = {
            'Index', 'area_no', 'ward_no', 'voter_count', 
            'voter_from_serial', 'voter_to_serial'
        }
        
        for col in numeric_cols_candidates:
            if col in self.candidates_df.columns:
                self.candidates_df[col] = pd.to_numeric(
                    self.candidates_df[col], errors='coerce'
                )
        
        numeric_cols_vc = {
            'area_no', 'ward_no', 'polling_center_code', 'voter_count',
            'voter_from_serial', 'voter_to_serial'
        }
        
        for col in numeric_cols_vc:
            if col in self.voting_centers_df.columns:
                self.voting_centers_df[col] = pd.to_numeric(
                    self.voting_centers_df[col], errors='coerce'
                )
        
        logger.info("Dataframes cleaned")
    
    # ============ COUNT QUERIES ============
    
    def count_candidates(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count candidates with optional filters.
        
        Args:
            filters: Dictionary of filter conditions
            
        Returns:
            Count of matching candidates
        """
        df = self._apply_filters(self.candidates_df, filters)
        count = len(df)
        logger.info(f"Count candidates with filters {filters}: {count}")
        return count
    
    def count_voting_centers(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count voting centers with optional filters.
        
        Args:
            filters: Dictionary of filter conditions
            
        Returns:
            Count of matching voting centers
        """
        df = self._apply_filters(self.voting_centers_df, filters)
        count = len(df)
        logger.info(f"Count voting centers with filters {filters}: {count}")
        return count
    
    # ============ EXACT LOOKUP ============
    
    def exact_lookup(self, 
                     column: str, 
                     value: str, 
                     target: str = "candidates",
                     limit: int = 10) -> List[Dict[str, Any]]:
        """
        Exact lookup by column value.
        
        Args:
            column: Column name to search in
            value: Value to search for
            target: 'candidates' or 'voting_centers'
            limit: Maximum number of results
            
        Returns:
            List of matching records
        """
        df = self.candidates_df if target == "candidates" else self.voting_centers_df
        
        if column not in df.columns:
            logger.warning(f"Column '{column}' not found in {target}")
            return []
        
        # Exact match (case-insensitive)
        matches = df[
            df[column].astype(str).str.contains(value, case=False, na=False, regex=False)
        ].head(limit)
        
        logger.info(f"Exact lookup in {target}.{column} for '{value}': {len(matches)} matches")
        return matches.to_dict(orient='records')
    
    def keyword_search(self, 
                      keyword: str, 
                      columns: Optional[List[str]] = None,
                      target: str = "candidates",
                      limit: int = 10) -> List[Dict[str, Any]]:
        """
        Keyword search using string matching.
        
        Args:
            keyword: Keyword to search for
            columns: List of columns to search in (all text columns if None)
            target: 'candidates' or 'voting_centers'
            limit: Maximum number of results
            
        Returns:
            List of matching records
        """
        df = self.candidates_df if target == "candidates" else self.voting_centers_df
        
        if not columns:
            # Search in all text columns
            columns = df.select_dtypes(include=['object']).columns.tolist()
        
        # Build boolean mask for keyword matching
        mask = pd.Series(False, index=df.index)
        
        for col in columns:
            if col in df.columns:
                mask |= df[col].astype(str).str.contains(
                    keyword, case=False, na=False, regex=False
                )
        
        matches = df[mask].head(limit)
        
        logger.info(f"Keyword search in {target} for '{keyword}': {len(matches)} matches")
        return matches.to_dict(orient='records')
    
    def fuzzy_search(self, 
                    search_term: str,
                    column: str,
                    target: str = "candidates",
                    threshold: float = 0.85,
                    limit: int = 10) -> List[Dict[str, Any]]:
        """
        Fuzzy search using string similarity.
        
        Handles typos and partial matches.
        
        Args:
            search_term: Term to search for
            column: Column to search in
            target: 'candidates' or 'voting_centers'
            threshold: Similarity threshold (0-1)
            limit: Maximum number of results
            
        Returns:
            List of matching records
        """
        df = self.candidates_df if target == "candidates" else self.voting_centers_df
        
        if column not in df.columns:
            logger.warning(f"Column '{column}' not found in {target}")
            return []
        
        # Extract unique values from column
        unique_values = df[column].dropna().unique().tolist()
        
        # Find best matches using RapidFuzz
        matches = process.extract(
            query=search_term,
            choices=unique_values,
            scorer=fuzz.WRatio,
            limit=limit
        )
        
        # Filter by threshold and get matching rows
        matched_values = [match[0] for match in matches if match[1] >= threshold]
        
        if not matched_values:
            logger.info(f"Fuzzy search: no matches above threshold {threshold}")
            return []
        
        # Return rows with matched values
        matched_rows = df[df[column].isin(matched_values)]
        
        logger.info(f"Fuzzy search in {target}.{column}: {len(matched_rows)} matches")
        return matched_rows.to_dict(orient='records')
    
    # ============ AGGREGATION ============
    
    def aggregate_by_field(self, 
                        field: str, 
                        target: str = "candidates",
                        filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        Aggregate counts by field.
        
        Args:
            field: Field to group by
            target: 'candidates' or 'voting_centers'
            filters: Optional filters to apply
            
        Returns:
            Dictionary mapping field values to counts
        """
        df = self.candidates_df if target == "candidates" else self.voting_centers_df
        df = self._apply_filters(df, filters)
        
        if field not in df.columns:
            logger.warning(f"Field '{field}' not found in {target}")
            return {}
        
        # Aggregate
        aggregation = df[field].value_counts().to_dict()
        
        logger.info(f"Aggregated by {field}: {len(aggregation)} groups")
        return aggregation
    
    # ============ STATISTICS ============
    
    def get_statistics(self, 
                     field: str, 
                     target: str = "candidates",
                     filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistical measures for numeric field.
        
        Args:
            field: Numeric field to analyze
            target: 'candidates' or 'voting_centers'
            filters: Optional filters to apply
            
        Returns:
            Dictionary with statistical measures
        """
        df = self.candidates_df if target == "candidates" else self.voting_centers_df
        df = self._apply_filters(df, filters)
        
        if field not in df.columns:
            logger.warning(f"Field '{field}' not found in {target}")
            return {}
        
        # Ensure numeric
        numeric_series = pd.to_numeric(df[field], errors='coerce').dropna()
        
        if len(numeric_series) == 0:
            logger.warning(f"No valid numeric data for field '{field}'")
            return {}
        
        stats = {
            "count": int(numeric_series.count()),
            "mean": float(numeric_series.mean()),
            "median": float(numeric_series.median()),
            "min": float(numeric_series.min()),
            "max": float(numeric_series.max()),
            "std": float(numeric_series.std()),
            "q25": float(numeric_series.quantile(0.25)),
            "q75": float(numeric_series.quantile(0.75)),
        }
        
        logger.info(f"Statistics for {field}: {stats}")
        return stats
    
    # ============ COMPARISON ============
    
    def compare_entities(self, 
                      entity_type: str, 
                      entities: List[str],
                      metric: str = "count",
                      filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Compare entities by a metric.
        
        Args:
            entity_type: Type of entities (party, district, province)
            entities: List of entity names to compare
            metric: Metric to compare (count, mean_age, etc.)
            filters: Optional filters to apply
            
        Returns:
            Dictionary mapping entities to metric values
        """
        df = self.candidates_df.copy()
        df = self._apply_filters(df, filters)
        
        results = {}
        
        # Map entity types to columns
        entity_column_map = {
            "party": ["Political Party", "Political Party In English"],
            "district": ["District", "District in English"],
            "province": ["State", "State in English", "State name in Nepali"],
        }
        
        # Get columns to search in
        search_columns = entity_column_map.get(entity_type.lower(), [])
        
        # Find matching columns in dataframe
        available_columns = [col for col in search_columns if col in df.columns]
        
        if not available_columns:
            logger.warning(f"No columns found for entity type '{entity_type}'")
            return {}
        
        for entity in entities:
            # Build filter for this entity
            entity_mask = pd.Series(False, index=df.index)
            
            for col in available_columns:
                entity_mask |= df[col].astype(str).str.contains(
                    entity, case=False, na=False, regex=False
                )
            
            entity_df = df[entity_mask]
            
            # Calculate metric
            if metric == "count":
                results[entity] = len(entity_df)
            elif metric in entity_df.columns:
                # For numeric metrics
                numeric_values = pd.to_numeric(entity_df[metric], errors='coerce').dropna()
                
                if len(numeric_values) > 0:
                    if metric in ["age", "Age"]:
                        # Check for age-related columns
                        age_cols = ["age", "DOB", "DOB"]
                        for age_col in age_cols:
                            if age_col in entity_df.columns:
                                numeric_values = pd.to_numeric(entity_df[age_col], errors='coerce').dropna()
                                break
                    
                    results[entity] = float(numeric_values.mean())
                else:
                    results[entity] = len(entity_df)
            else:
                # Count as default
                results[entity] = len(entity_df)
        
        logger.info(f"Compared {len(entities)} {entity_type} by {metric}")
        return results
    
    # ============ FILTERING ============
    
    def _apply_filters(self, df: pd.DataFrame, filters: Optional[Dict[str, Any]]) -> pd.DataFrame:
        """
        Apply filters to dataframe.
        
        Args:
            df: DataFrame to filter
            filters: Dictionary of filter conditions
            
        Returns:
            Filtered DataFrame
        """
        if not filters:
            return df.copy()
        
        df_filtered = df.copy()
        
        for column, value in filters.items():
            if column not in df_filtered.columns:
                continue
            
            if isinstance(value, list):
                # Filter by list of values
                df_filtered = df_filtered[df_filtered[column].isin(value)]
            elif isinstance(value, dict):
                # Handle range filters
                if "min" in value:
                    df_filtered = df_filtered[pd.to_numeric(df_filtered[column], errors='coerce') >= value["min"]]
                if "max" in value:
                    df_filtered = df_filtered[pd.to_numeric(df_filtered[column], errors='coerce') <= value["max"]]
                if "gt" in value:  # Greater than
                    df_filtered = df_filtered[pd.to_numeric(df_filtered[column], errors='coerce') > value["gt"]]
                if "lt" in value:  # Less than
                    df_filtered = df_filtered[pd.to_numeric(df_filtered[column], errors='coerce') < value["lt"]]
            elif isinstance(value, str):
                # String matching (case-insensitive, partial match)
                df_filtered = df_filtered[
                    df_filtered[column].astype(str).str.contains(
                        value, case=False, na=False, regex=False
                    )
                ]
            elif isinstance(value, (int, float)):
                # Exact match for numbers
                df_filtered = df_filtered[pd.to_numeric(df_filtered[column], errors='coerce') == value]
            elif isinstance(value, bool):
                # Boolean match
                df_filtered = df_filtered[df_filtered[column] == value]
        
        logger.debug(f"Applied filters: {filters}, result: {len(df_filtered)} rows")
        return df_filtered
    
    # ============ UTILITY ============
    
    def get_top_n(self, 
                  field: str, 
                  n: int = 10,
                  target: str = "candidates",
                  ascending: bool = False,
                  filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get top N entries by field value.
        
        Args:
            field: Field to sort by
            n: Number of entries to return
            target: 'candidates' or 'voting_centers'
            ascending: Sort ascending or descending
            filters: Optional filters to apply
            
        Returns:
            List of top N records
        """
        df = self.candidates_df if target == "candidates" else self.voting_centers_df
        df = self._apply_filters(df, filters)
        
        if field not in df.columns:
            logger.warning(f"Field '{field}' not found in {target}")
            return []
        
        # Ensure numeric
        df[field] = pd.to_numeric(df[field], errors='coerce')
        
        # Sort and get top N
        top_n = df.nlargest(n, field) if not ascending else df.nsmallest(n, field)
        
        logger.info(f"Top {n} by {field} ({'ascending' if ascending else 'descending'})")
        return top_n.to_dict(orient='records')
