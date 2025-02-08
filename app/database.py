import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fetch database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")


def get_db_connection():
    """Return a connection to the PostgreSQL database."""
    conn = psycopg2.connect(DATABASE_URL)
    return conn


def create_tables():
    """Create necessary tables in the database."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Create table for storing document vectors
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_vectors (
                document_id UUID PRIMARY KEY,
                user_id UUID NOT NULL,
                vector BYTEA,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()
    finally:
        conn.close()


def cleanup_old_vectors():
    """Delete vectors that are older than 7 days."""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()

        # Delete vectors that are older than 7 days
        cursor.execute("""
            DELETE FROM document_vectors
            WHERE created_at < NOW() - INTERVAL '7 days';
        """)
        conn.commit()
    finally:
        conn.close()
