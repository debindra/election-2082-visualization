"""
SQLite Service for Query Execution

Handles SQL query execution for structured data queries.
"""
import logging
import sqlite3
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from contextlib import contextmanager
import time

from config.settings import settings
from services.sqlite_pool import get_connection_pool
from services.redis_cache import RedisCacheService

logger = logging.getLogger(__name__)


class SQLiteService:
    """
    Service for executing SQL queries on election data.
    
    Provides methods for common query patterns and raw SQL execution.
    Uses connection pooling for better performance.
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize SQLite service.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path or str(Path("data/elections/election_data.db"))
        
        # Get connection pool
        self.pool = get_connection_pool(db_path=self.db_path)
        
        # Initialize Redis cache
        self.cache = RedisCacheService()
        
        # Check if database exists
        if not Path(self.db_path).exists():
            logger.warning(f"Database not found at {self.db_path}. Run setup_sqlite.py first.")
        
        logger.info(f"SQLite service initialized with database: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connection.
        
        Uses connection pool for better performance.
        """
        with self.pool.get_connection() as conn:
            yield conn
    
    def execute_query(self,
                    query: str,
                    params: Optional[Tuple] = None,
                    fetch: str = "all",
                    use_cache: bool = True) -> List[Dict[str, Any]]:
        """
        Execute a raw SQL query safely.

        Args:
            query: SQL query string (use ? for parameters)
            params: Query parameters for prepared statement
            fetch: 'all', 'one', or None
            use_cache: Whether to use query result caching

        Returns:
            List of dictionaries (rows) or None
        """
        # Try cache first for SELECT queries
        if use_cache and self.cache.enabled:
            if query.strip().upper().startswith('SELECT'):
                cached_result = self.cache.get_cached_sql_result(query, params or ())
                if cached_result is not None:
                    logger.debug("SQL query cache hit")
                    return cached_result

        start_time = time.time()

        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()

                # Execute with parameters if provided (handles both tuple and list)
                if params is not None:
                    # Convert list to tuple if needed
                    if isinstance(params, list):
                        params = tuple(params)
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if fetch == "all":
                    rows = cursor.fetchall()
                    result = [dict(row) for row in rows]
                elif fetch == "one":
                    row = cursor.fetchone()
                    result = dict(row) if row else None
                else:
                    conn.commit()
                    result = []

                # Log slow queries
                elapsed_ms = (time.time() - start_time) * 1000
                if settings.enable_performance_metrics and elapsed_ms > settings.slow_query_threshold_ms:
                    logger.warning(f"Slow SQL query ({elapsed_ms:.1f}ms): {query[:100]}...")

                # Cache SELECT results
                if use_cache and self.cache.enabled:
                    if query.strip().upper().startswith('SELECT') and fetch in ("all", "one"):
                        self.cache.cache_sql_result(query, params or (), result)

                return result

        except sqlite3.Error as e:
            logger.error(f"SQL error: {e}\nQuery: {query}\nParams: {params}")
            raise
    
    # ============ COUNT QUERIES ============
    
    def count_candidates(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count candidates with optional filters.
        
        Args:
            filters: Dictionary of field-value pairs for filtering
            
        Returns:
            Count of matching candidates
        """
        query = "SELECT COUNT(*) as count FROM candidates"
        params = None
        if filters:
            where_clause, params = self._build_where_clause(filters)
            query += " WHERE " + where_clause
        
        result = self.execute_query(query, params=params)
        return result[0]["count"] if result else 0
    
    def count_voting_centers(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """
        Count voting centers with optional filters.
        
        Args:
            filters: Dictionary of field-value pairs for filtering
            
        Returns:
            Count of matching voting centers
        """
        query = "SELECT COUNT(*) as count FROM voting_centers"
        params = None
        if filters:
            where_clause, params = self._build_where_clause(filters)
            query += " WHERE " + where_clause
        
        result = self.execute_query(query, params=params)
        return result[0]["count"] if result else 0
    
    # ============ EXACT LOOKUP ============
    
    def exact_lookup(self,
                   table: str,
                   column: str,
                   value: str,
                   limit: int = 10) -> List[Dict[str, Any]]:
        """
        Exact lookup by column value.
        
        Args:
            table: 'candidates' or 'voting_centers'
            column: Column name to search
            value: Value to search for
            limit: Maximum results
            
        Returns:
            List of matching records
        """
        if table not in ["candidates", "voting_centers"]:
            raise ValueError(f"Invalid table: {table}")
        
        query = f"""
            SELECT * FROM {table}
            WHERE {column} LIKE ? COLLATE NOCASE
            LIMIT ?
        """
        
        return self.execute_query(query, params=(f"%{value}%", limit))
    
    # ============ FULL-TEXT SEARCH ============
    
    def full_text_search(self,
                       table: str,
                       search_term: str,
                       limit: int = 10) -> List[Dict[str, Any]]:
        """
        Full-text search using FTS5.
        
        Args:
            table: 'candidates' or 'voting_centers'
            search_term: Text to search for
            limit: Maximum results
            
        Returns:
            List of matching records
        """
        if table not in ["candidates", "voting_centers"]:
            raise ValueError(f"Invalid table: {table}")
        
        fts_table = f"{table}_fts"
        
        query = f"""
            SELECT t.* FROM {table} t
            JOIN {fts_table} fts ON t.id = fts.rowid
            WHERE {fts_table} MATCH ?
            ORDER BY rank
            LIMIT ?
        """
        
        return self.execute_query(query, params=(search_term, limit))
    
    # ============ AGGREGATION ============
    
    def aggregate_by_field(self,
                        table: str,
                        field: str,
                        filters: Optional[Dict[str, Any]] = None) -> Dict[str, int]:
        """
        Aggregate counts by field.
        
        Args:
            table: 'candidates' or 'voting_centers'
            field: Field to group by
            filters: Optional filters
            
        Returns:
            Dictionary mapping field values to counts
        """
        if table not in ["candidates", "voting_centers"]:
            raise ValueError(f"Invalid table: {table}")
        
        query = f"""
            SELECT {field}, COUNT(*) as count
            FROM {table}
        """
        
        params = None
        if filters:
            where_clause, params = self._build_where_clause(filters)
            query += " WHERE " + where_clause
        
        query += f" GROUP BY {field} ORDER BY count DESC"
        
        results = self.execute_query(query)
        return {row[field]: row["count"] for row in results}
    
    # ============ STATISTICS ============
    
    def get_statistics(self,
                     table: str,
                     field: str,
                     filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get statistical measures for numeric field.
        
        Args:
            table: 'candidates' or 'voting_centers'
            field: Numeric field
            filters: Optional filters
            
        Returns:
            Dictionary with statistics
        """
        if table not in ["candidates", "voting_centers"]:
            raise ValueError(f"Invalid table: {table}")
        
        query = f"""
            SELECT 
                COUNT(*) as count,
                AVG({field}) as mean,
                MIN({field}) as min,
                MAX({field}) as max,
                ROUND(STDDEV({field}), 2) as std
            FROM {table}
        """
        
        params = None
        if filters:
            where_clause, params = self._build_where_clause(filters)
            query += " WHERE " + where_clause
        
        result = self.execute_query(query, params=params)
        row = result[0] if result else None
        
        if not row or row["count"] == 0:
            return {}
        
        return row
    
    # ============ COMPARISON ============
    
    def compare_entities(self,
                      table: str,
                      column: str,
                      entities: List[str],
                      metric: str = "count") -> Dict[str, Any]:
        """
        Compare entities by a metric.
        
        Args:
            table: 'candidates' or 'voting_centers'
            column: Column to filter by
            entities: List of entity values
            metric: 'count' or numeric column name
            
        Returns:
            Dictionary mapping entities to metric values
        """
        if table not in ["candidates", "voting_centers"]:
            raise ValueError(f"Invalid table: {table}")
        
        results = {}
        
        for entity in entities:
            if metric == "count":
                query = f"""
                    SELECT COUNT(*) as value FROM {table}
                    WHERE {column} LIKE ?
                """
                result = self.execute_query(query, params=(f"%{entity}%",), fetch="one")
                results[entity] = result["value"] if result else 0
            else:
                query = f"""
                    SELECT AVG({metric}) as value FROM {table}
                    WHERE {column} LIKE ? AND {metric} IS NOT NULL
                """
                result = self.execute_query(query, params=(f"%{entity}%",), fetch="one")
                results[entity] = result["value"] if result and result["value"] else 0
        
        return results
    
    # ============ TOP N ============
    
    def get_top_n(self,
                 table: str,
                 field: str,
                 n: int = 10,
                 ascending: bool = False,
                 filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Get top N entries by field value.
        
        Args:
            table: 'candidates' or 'voting_centers'
            field: Field to sort by
            n: Number of results
            ascending: Sort order
            filters: Optional filters
            
        Returns:
            List of top N records
        """
        if table not in ["candidates", "voting_centers"]:
            raise ValueError(f"Invalid table: {table}")
        
        order = "ASC" if ascending else "DESC"
        query = f"SELECT * FROM {table}"
        
        params = None
        if filters:
            where_clause, params = self._build_where_clause(filters)
            query += " WHERE " + where_clause
        
        query += f" ORDER BY {field} {order} LIMIT {n}"
        
        return self.execute_query(query, params=params)
    
    # ============ UTILITY METHODS ============
    
    def _build_where_clause(self, filters: Dict[str, Any]) -> Tuple[str, List]:
        """
        Build WHERE clause and params from filters dictionary.
        
        Args:
            filters: Dictionary of field-value pairs
            
        Returns:
            Tuple of (where_clause, params_list)
        """
        conditions = []
        params = []
        
        for field, value in filters.items():
            if isinstance(value, list):
                placeholders = ', '.join(['?' for _ in value])
                conditions.append(f"{field} IN ({placeholders})")
                params.extend(value)
            elif isinstance(value, dict):
                # Handle range filters
                if "min" in value:
                    conditions.append(f"{field} >= ?")
                    params.append(value["min"])
                if "max" in value:
                    conditions.append(f"{field} <= ?")
                    params.append(value["max"])
                if "gt" in value:
                    conditions.append(f"{field} > ?")
                    params.append(value["gt"])
                if "lt" in value:
                    conditions.append(f"{field} < ?")
                    params.append(value["lt"])
            else:
                conditions.append(f"{field} LIKE ?")
                params.append(f"%{value}%")
        
        where_clause = " AND ".join(conditions)
        return where_clause, params
    
    def get_table_info(self, table: str) -> List[Dict[str, Any]]:
        """
        Get table schema information.
        
        Args:
            table: Table name
            
        Returns:
            List of column information
        """
        query = f"PRAGMA table_info({table})"
        return self.execute_query(query)
    
    def get_schema_for_prompt(self) -> str:
        """
        Get formatted schema for LLM prompting.
        
        Returns:
            Formatted schema string
        """
        candidates_info = self.get_table_info("candidates")
        voting_centers_info = self.get_table_info("voting_centers")
        
        schema = """
=== DATABASE SCHEMA ====

Table: candidates
Columns:
"""
        for col in candidates_info:
            schema += f"  - {col['name']} ({col['type']})\n"
        
        schema += "\nTable: voting_centers\nColumns:\n"
        for col in voting_centers_info:
            schema += f"  - {col['name']} ({col['type']})\n"
        
        schema += """
=== AVAILABLE TABLES ====
- candidates: Election candidate information
- voting_centers: Voting center/booth information

=== FULL-TEXT SEARCH TABLES ====
- candidates_fts: Full-text search on candidates table
- voting_centers_fts: Full-text search on voting_centers table

=== NOTES ====
- Use LIKE operator for case-insensitive text matching
- Full-text search uses MATCH operator on *_fts tables
- Both Nepali and English columns available
- voter_count is numeric field in voting_centers
"""
        return schema
    
    def validate_query(self, query: str) -> Tuple[bool, Optional[str]]:
        """
        Validate a SQL query before execution.

        Args:
            query: SQL query to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'INSERT', 'UPDATE',
            'CREATE', 'GRANT', 'REVOKE', 'ATTACH', 'DETACH'
        ]

        query_upper = query.upper()
        for keyword in dangerous_keywords:
            if keyword in query_upper:
                return False, f"Query contains forbidden keyword: {keyword}"

        # Check if query starts with SELECT (read-only)
        if not query.strip().upper().startswith('SELECT'):
            return False, "Only SELECT queries are allowed"

        # Try to execute with EXPLAIN (doesn't actually run)
        # Need to handle placeholders - replace them with dummy values for validation
        try:
            import re
            # Count placeholders
            placeholder_count = query.count('?')
            if placeholder_count > 0:
                # Create dummy values for validation
                dummy_params = tuple([''] * placeholder_count)
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"EXPLAIN QUERY PLAN {query}", dummy_params)
            else:
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"EXPLAIN QUERY PLAN {query}")
            return True, None
        except sqlite3.Error as e:
            return False, f"Query validation failed: {str(e)}"
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get connection pool statistics.
        
        Returns:
            Dictionary with pool statistics
        """
        return self.pool.get_stats()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        return self.cache.get_stats()