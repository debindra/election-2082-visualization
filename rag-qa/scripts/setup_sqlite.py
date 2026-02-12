"""
SQLite Database Setup Script

Creates SQLite database from CSV files with proper schema, indexes, and FTS.
"""
import logging
import sys
from pathlib import Path
import sqlite3
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config.settings import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_candidates_schema():
    """
    Returns SQL schema for candidates table.
    """
    return """
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate_full_name TEXT NOT NULL,
        gender TEXT,
        election_area TEXT,
        area_no INTEGER,
        state TEXT,
        state_in_english TEXT,
        district TEXT,
        district_in_english TEXT,
        dob TEXT,
        birth_place TEXT,
        birth_place_in_english TEXT,
        permanent_address TEXT,
        parent_name TEXT,
        spouse_name TEXT,
        spouse_name_in_english TEXT,
        political_party TEXT,
        political_party_in_english TEXT,
        election_symbol TEXT,
        academic_qualification TEXT,
        academic_qualification_generalized TEXT,
        university TEXT,
        experience TEXT,
        image_url TEXT,
        candidate_full_name_in_english TEXT,
        spouse_index TEXT
    )
    """


def get_voting_centers_schema():
    """
    Returns SQL schema for voting_centers table.
    """
    return """
    CREATE TABLE IF NOT EXISTS voting_centers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area_no INTEGER NOT NULL,
        district TEXT NOT NULL,
        district_name_english TEXT,
        province TEXT,
        palika_type TEXT,
        palika_name TEXT,
        palika_name_en TEXT,
        ward_no INTEGER,
        polling_center_code INTEGER,
        polling_center_name TEXT,
        sub_center TEXT,
        voter_count INTEGER,
        voter_from_serial INTEGER,
        voter_to_serial INTEGER,
        source_file TEXT,
        language TEXT
    )
    """


def create_indexes(conn):
    """
    Create indexes for optimal query performance.
    """
    logger.info("Creating indexes...")
    
    cursor = conn.cursor()
    
    # Candidates indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_candidates_district ON candidates(district)",
        "CREATE INDEX IF NOT EXISTS idx_candidates_district_en ON candidates(district_in_english)",
        "CREATE INDEX IF NOT EXISTS idx_candidates_state ON candidates(state)",
        "CREATE INDEX IF NOT EXISTS idx_candidates_state_en ON candidates(state_in_english)",
        "CREATE INDEX IF NOT EXISTS idx_candidates_party ON candidates(political_party)",
        "CREATE INDEX IF NOT EXISTS idx_candidates_party_en ON candidates(political_party_in_english)",
        "CREATE INDEX IF NOT EXISTS idx_candidates_gender ON candidates(gender)",
        "CREATE INDEX IF NOT EXISTS idx_candidates_area_no ON candidates(area_no)",
        "CREATE INDEX IF NOT EXISTS idx_candidates_name ON candidates(candidate_full_name)",
        "CREATE INDEX IF NOT EXISTS idx_candidates_name_en ON candidates(candidate_full_name_in_english)",
    ]
    
    # Voting centers indexes
    vc_indexes = [
        "CREATE INDEX IF NOT EXISTS idx_vc_area_no ON voting_centers(area_no)",
        "CREATE INDEX IF NOT EXISTS idx_vc_district ON voting_centers(district)",
        "CREATE INDEX IF NOT EXISTS idx_vc_district_en ON voting_centers(district_name_english)",
        "CREATE INDEX IF NOT EXISTS idx_vc_province ON voting_centers(province)",
        "CREATE INDEX IF NOT EXISTS idx_vc_palika_type ON voting_centers(palika_type)",
        "CREATE INDEX IF NOT EXISTS idx_vc_palika_name ON voting_centers(palika_name)",
        "CREATE INDEX IF NOT EXISTS idx_vc_palika_name_en ON voting_centers(palika_name_en)",
        "CREATE INDEX IF NOT EXISTS idx_vc_ward_no ON voting_centers(ward_no)",
        "CREATE INDEX IF NOT EXISTS idx_vc_polling_code ON voting_centers(polling_center_code)",
        "CREATE INDEX IF NOT EXISTS idx_vc_voter_count ON voting_centers(voter_count)",
    ]
    
    for idx_sql in indexes + vc_indexes:
        cursor.execute(idx_sql)
    
    conn.commit()
    logger.info(f"Created {len(indexes + vc_indexes)} indexes")


def create_full_text_search(conn):
    """
    Create full-text search tables for better text search.
    """
    logger.info("Creating full-text search tables...")
    
    cursor = conn.cursor()
    
    # FTS for candidates
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS candidates_fts 
        USING fts5(
            candidate_full_name,
            candidate_full_name_in_english,
            district,
            district_in_english,
            political_party,
            political_party_in_english,
            academic_qualification,
            experience,
            content='candidates',
            content_rowid='id'
        )
    """)
    
    # FTS for voting centers
    cursor.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS voting_centers_fts 
        USING fts5(
            district,
            district_name_english,
            province,
            palika_name,
            palika_name_en,
            polling_center_name,
            content='voting_centers',
            content_rowid='id'
        )
    """)
    
    # Populate FTS tables
    cursor.execute("""
        INSERT INTO candidates_fts(rowid, candidate_full_name, candidate_full_name_in_english, 
                                  district, district_in_english, political_party, 
                                  political_party_in_english, academic_qualification, experience)
        SELECT id, candidate_full_name, candidate_full_name_in_english, 
               district, district_in_english, political_party, 
               political_party_in_english, academic_qualification, experience
        FROM candidates
    """)
    
    cursor.execute("""
        INSERT INTO voting_centers_fts(rowid, district, district_name_english, 
                                      province, palika_name, palika_name_en, polling_center_name)
        SELECT id, district, district_name_english, 
               province, palika_name, palika_name_en, polling_center_name
        FROM voting_centers
    """)
    
    conn.commit()
    logger.info("Full-text search tables created and populated")


def import_candidates(conn, csv_path):
    """
    Import candidates from CSV to SQLite.
    """
    logger.info(f"Importing candidates from {csv_path}...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} candidates from CSV")
    
    # Clean column names (remove trailing/leading spaces)
    df.columns = df.columns.str.strip()
    
    # Map CSV columns to SQLite columns
    column_mapping = {
        'Index': None,  # Skip - we use auto-increment id
        'Candidate Full Name': 'candidate_full_name',
        'Gender': 'gender',
        'Election Area': 'election_area',
        'area_no': 'area_no',
        'State': 'state',
        'State in English': 'state_in_english',
        'District': 'district',
        'District in English': 'district_in_english',
        'DOB': 'dob',
        'Birth Place': 'birth_place',
        'Birth Place In english': 'birth_place_in_english',
        'Permanent Address': 'permanent_address',
        'Parent\'s Name': 'parent_name',
        'Spouse Name': 'spouse_name',
        'Spouse Name in English': 'spouse_name_in_english',
        'Political Party': 'political_party',
        'Political Party In English': 'political_party_in_english',
        'Election Symbol': 'election_symbol',
        'Academic qualification': 'academic_qualification',
        'Academic Qualification Generalized': 'academic_qualification_generalized',
        'University': 'university',
        'Experience': 'experience',
        'Image URL': 'image_url',
        'Candidate Full Name in English': 'candidate_full_name_in_english',
        'spouse_index': 'spouse_index',
    }
    
    # Rename columns
    df_renamed = df.rename(columns=column_mapping)
    
    # Drop unmapped columns
    df_clean = df_renamed[[col for col in df_renamed.columns if col in column_mapping.values() or col == 'Unnamed: 17']]
    
    # Drop the unnamed column if exists
    df_clean = df_clean.drop(columns=[col for col in df_clean.columns if 'Unnamed' in col], errors='ignore')
    
    # Insert into database
    cursor = conn.cursor()
    
    # Prepare columns and placeholders
    columns = df_clean.columns.tolist()
    placeholders = ', '.join(['?' for _ in columns])
    columns_str = ', '.join(columns)
    
    # Insert data
    data = df_clean.where(pd.notnull(df_clean), None).values.tolist()
    cursor.executemany(
        f"INSERT INTO candidates ({columns_str}) VALUES ({placeholders})",
        data
    )
    
    conn.commit()
    logger.info(f"✓ Imported {len(data)} candidates to SQLite")


def import_voting_centers(conn, csv_path):
    """
    Import voting centers from CSV to SQLite.
    """
    logger.info(f"Importing voting centers from {csv_path}...")
    
    # Read CSV
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} voting centers from CSV")
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Map CSV columns to SQLite columns
    column_mapping = {
        'area_no': 'area_no',
        'district': 'district',
        'district_name_english': 'district_name_english',
        'province': 'province',
        'palika_type': 'palika_type',
        'palika_name': 'palika_name',
        'palika_name_en': 'palika_name_en',
        'ward_no': 'ward_no',
        'polling_center_code': 'polling_center_code',
        'polling_center_name': 'polling_center_name',
        'sub_center': 'sub_center',
        'voter_count': 'voter_count',
        'voter_from_serial': 'voter_from_serial',
        'voter_to_serial': 'voter_to_serial',
        'source_file': 'source_file',
        'language': 'language',
    }
    
    # Rename columns
    df_renamed = df.rename(columns=column_mapping)
    
    # Drop unmapped columns
    df_clean = df_renamed[[col for col in df_renamed.columns if col in column_mapping.values()]]
    
    # Insert into database
    cursor = conn.cursor()
    
    # Prepare columns and placeholders
    columns = df_clean.columns.tolist()
    placeholders = ', '.join(['?' for _ in columns])
    columns_str = ', '.join(columns)
    
    # Insert data
    data = df_clean.where(pd.notnull(df_clean), None).values.tolist()
    cursor.executemany(
        f"INSERT INTO voting_centers ({columns_str}) VALUES ({placeholders})",
        data
    )
    
    conn.commit()
    logger.info(f"✓ Imported {len(data)} voting centers to SQLite")


def get_db_stats(conn):
    """
    Get database statistics.
    """
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM candidates")
    candidates_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM voting_centers")
    vc_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name IN ('candidates', 'voting_centers')")
    index_count = cursor.fetchone()[0]
    
    # Get database file size
    db_path = conn.execute("PRAGMA database_list").fetchone()[2]
    if db_path and Path(db_path).exists():
        db_size = Path(db_path).stat().st_size / (1024 * 1024)  # MB
    else:
        db_size = 0
    
    return {
        "candidates": candidates_count,
        "voting_centers": vc_count,
        "indexes": index_count,
        "db_size_mb": round(db_size, 2)
    }


def main():
    """
    Main function to set up SQLite database.
    """
    db_path = Path("data/elections/election_data.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info("=" * 60)
    logger.info("SQLite Database Setup")
    logger.info("=" * 60)
    logger.info(f"Database Path: {db_path.absolute()}")
    
    # Check if database already exists
    if db_path.exists():
        logger.warning(f"Database already exists at {db_path}")
        response = input("Do you want to recreate it? This will delete all existing data. (y/N): ")
        if response.lower() != 'y':
            logger.info("Setup cancelled")
            return
    
    # Create database connection
    conn = sqlite3.connect(str(db_path))
    
    try:
        # Create tables
        logger.info("Creating tables...")
        conn.execute(get_candidates_schema())
        conn.execute(get_voting_centers_schema())
        conn.commit()
        logger.info("✓ Tables created")
        
        # Import data
        import_candidates(conn, settings.candidates_csv)
        import_voting_centers(conn, settings.voting_centers_csv)
        
        # Create indexes
        create_indexes(conn)
        
        # Create FTS
        create_full_text_search(conn)
        
        # Show statistics
        stats = get_db_stats(conn)
        logger.info("")
        logger.info("=" * 60)
        logger.info("Database Statistics")
        logger.info("=" * 60)
        logger.info(f"Candidates: {stats['candidates']:,}")
        logger.info(f"Voting Centers: {stats['voting_centers']:,}")
        logger.info(f"Indexes: {stats['indexes']}")
        logger.info(f"Database Size: {stats['db_size_mb']:.2f} MB")
        logger.info("=" * 60)
        logger.info("✓ Database setup completed successfully!")
        
    except Exception as e:
        logger.error(f"Error setting up database: {e}", exc_info=True)
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
