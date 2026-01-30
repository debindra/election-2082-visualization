"""
Data loading module for election CSV files.

Handles loading CSV files by election year, with validation and preprocessing.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from app.core.config import ELECTIONS_DIR
from app.core.settings import settings
from app.data.validator import validate_csv_columns, ValidationResult
from app.data.preprocess import preprocess_election_data

logger = logging.getLogger(__name__)


class ElectionDataLoader:
    """Loader for election CSV data files."""
    
    def __init__(self, elections_dir: Optional[Path] = None):
        """
        Initialize loader.
        
        Args:
            elections_dir: Directory containing election CSV files
        """
        self.elections_dir = elections_dir or ELECTIONS_DIR
        self._cache: Dict[int, pd.DataFrame] = {}
        self._validation_cache: Dict[int, ValidationResult] = {}
    
    def list_available_elections(self) -> List[int]:
        """
        List available election years based on CSV files.
        
        Returns:
            List of election years found
        """
        election_years = []
        
        if not self.elections_dir.exists():
            logger.warning(f"Elections directory does not exist: {self.elections_dir}")
            return election_years
        
        for csv_file in self.elections_dir.glob("*.csv"):
            # Try to extract year from filename
            filename = csv_file.stem
            import re
            year_match = re.search(r'\b(19|20)\d{2}\b', filename)
            if year_match:
                try:
                    year = int(year_match.group())
                    election_years.append(year)
                except ValueError:
                    logger.warning(f"Could not parse year from filename: {csv_file}")
        
        return sorted(election_years)
    
    def load_election(
        self,
        election_year: int,
        validate: bool = True,
        preprocess: bool = True,
        use_cache: bool = True,
    ) -> Tuple[pd.DataFrame, Optional[ValidationResult]]:
        """
        Load election data for a specific year.
        
        Args:
            election_year: Year of election
            validate: Whether to validate CSV structure
            preprocess: Whether to preprocess data
            use_cache: Whether to use cached data if available
            
        Returns:
            Tuple of (DataFrame, ValidationResult)
            
        Raises:
            FileNotFoundError: If CSV file not found
            ValueError: If validation fails in strict mode
        """
        # Check cache
        if use_cache and election_year in self._cache:
            logger.info(f"Using cached data for election {election_year}")
            validation = self._validation_cache.get(election_year)
            return self._cache[election_year].copy(), validation
        
        # Find CSV file
        csv_file = self._find_csv_file(election_year)
        if csv_file is None:
            raise FileNotFoundError(
                f"No CSV file found for election year {election_year} in {self.elections_dir}"
            )
        
        logger.info(f"Loading election data from {csv_file}")
        
        # Load CSV
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
        except UnicodeDecodeError:
            # Try alternative encodings
            try:
                df = pd.read_csv(csv_file, encoding='latin-1')
                logger.warning(f"Loaded {csv_file} with latin-1 encoding")
            except Exception as e:
                logger.error(f"Failed to load {csv_file}: {e}")
                raise
        
        validation = None
        
        # Validate
        if validate:
            validation = validate_csv_columns(df, csv_file, strict=settings.strict_validation)
            
            if not validation.is_valid and settings.strict_validation:
                raise ValueError(
                    f"Validation failed for {csv_file}: {validation.errors}"
                )
        
        # Preprocess
        if preprocess:
            df = preprocess_election_data(df, str(csv_file), election_year)
        
        # Cache
        if use_cache:
            self._cache[election_year] = df.copy()
            if validation:
                self._validation_cache[election_year] = validation
        
        return df, validation
    
    def load_all_elections(
        self,
        validate: bool = True,
        preprocess: bool = True,
    ) -> Dict[int, pd.DataFrame]:
        """
        Load all available election data.
        
        Args:
            validate: Whether to validate CSV structure
            preprocess: Whether to preprocess data
            
        Returns:
            Dictionary mapping election year to DataFrame
        """
        election_years = self.list_available_elections()
        
        if not election_years:
            logger.warning("No election data files found")
            return {}
        
        all_data = {}
        
        for year in election_years:
            try:
                df, _ = self.load_election(year, validate=validate, preprocess=preprocess)
                all_data[year] = df
            except Exception as e:
                logger.error(f"Failed to load election {year}: {e}")
                if settings.strict_validation:
                    raise
        
        return all_data
    
    def _find_csv_file(self, election_year: int) -> Optional[Path]:
        """
        Find CSV file for given election year.
        
        Args:
            election_year: Year of election
            
        Returns:
            Path to CSV file or None if not found
        """
        # Try exact match first
        patterns = [
            f"election_{election_year}.csv",
            f"election{election_year}.csv",
            f"{election_year}.csv",
        ]
        
        for pattern in patterns:
            csv_file = self.elections_dir / pattern
            if csv_file.exists():
                return csv_file
        
        # Try fuzzy match (contains year)
        for csv_file in self.elections_dir.glob("*.csv"):
            if str(election_year) in csv_file.stem:
                return csv_file
        
        return None
    
    def clear_cache(self):
        """Clear cached data."""
        self._cache.clear()
        self._validation_cache.clear()
        logger.info("Cache cleared")


# Global loader instance
loader = ElectionDataLoader()
