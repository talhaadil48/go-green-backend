import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from pathlib import Path
from contextlib import contextmanager
import time

# Load .env.local
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env.local"
load_dotenv(dotenv_path=ENV_PATH)


class DBConnection:
    _connection = None
    _max_retries = 3
    _retry_delay = 0.01  # seconds

    @classmethod
    def _connect(cls):
        """Create a new database connection."""
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise RuntimeError("DATABASE_URL not found in .env.local")

        try:
            cls._connection = psycopg2.connect(
                database_url,
                sslmode="require",
                cursor_factory=DictCursor
            )
            print("Database connected.")
        except psycopg2.Error as e:
            print("Error connecting to database:", e)
            raise

    @classmethod
    def get_connection(cls):
        """Return a live connection, reconnecting if necessary."""
        retries = 0
        while retries < cls._max_retries:
            try:
                if cls._connection is None or cls._connection.closed != 0:
                    cls._connect()
                else:
                    # Test connection by ping
                    with cls._connection.cursor() as cur:
                        cur.execute("SELECT 1")
                return cls._connection
            except psycopg2.OperationalError:
                print(f"Connection lost. Retrying in {cls._retry_delay} seconds...")
                cls._connection = None
                time.sleep(cls._retry_delay)
                retries += 1

        raise RuntimeError("Failed to connect to the database after multiple attempts.")

    @classmethod
    @contextmanager
    def get_cursor(cls):
        """
        Context manager for a cursor that ensures the connection is alive.
        Usage:
        with DBConnection.get_cursor() as cur:
            cur.execute(...)
        """
        conn = cls.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            cursor.close()

    @classmethod
    def close_connection(cls):
        """Closes the database connection if open."""
        if cls._connection and cls._connection.closed == 0:
            cls._connection.close()
            cls._connection = None
            print("Database connection closed.")