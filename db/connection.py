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
    def _ensure_clean_connection(cls, conn):
        """Ensure connection is in a clean state (no aborted transactions)."""
        try:
            # Test if connection works
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return conn
        except psycopg2.errors.InFailedSqlTransaction:
            # Transaction is aborted - roll it back
            print("⚠️ Aborted transaction detected, rolling back...")
            conn.rollback()
            # Verify it worked
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            return conn
        except psycopg2.OperationalError:
            # Connection is dead, will be recreated
            raise
        except Exception as e:
            # Any other error, try to rollback
            try:
                conn.rollback()
            except:
                pass
            raise e

    @classmethod
    def get_connection(cls):
        """Return a live connection, reconnecting if necessary."""
        retries = 0
        while retries < cls._max_retries:
            try:
                if cls._connection is None or cls._connection.closed != 0:
                    cls._connect()
                else:
                    # Ensure connection is clean before using
                    cls._connection = cls._ensure_clean_connection(cls._connection)
                return cls._connection
            except psycopg2.OperationalError:
                print(f"Connection lost. Retrying in {cls._retry_delay} seconds...")
                cls._connection = None
                time.sleep(cls._retry_delay)
                retries += 1
            except Exception as e:
                print(f"Error getting connection: {e}")
                cls._connection = None
                raise

        raise RuntimeError("Failed to connect to the database after multiple attempts.")

    @classmethod
    @contextmanager
    def get_cursor(cls):
        """
        Context manager for a cursor that ensures the connection is alive.
        Automatically handles transaction rollback on errors.
        Usage:
        with DBConnection.get_cursor() as cur:
            cur.execute(...)
        """
        conn = cls.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except psycopg2.errors.InFailedSqlTransaction:
            # Aborted transaction - rollback and re-raise
            print("⚠️ Aborted transaction in get_cursor, rolling back...")
            conn.rollback()
            raise
        except Exception as e:
            # Rollback on any error
            print(f"⚠️ Error in transaction, rolling back: {e}")
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


def split_car_name_and_model():
    query = """
        SELECT * FROM claims;
    """

    with DBConnection.get_cursor() as cur:
        cur.execute(query)
        curaims = cur.fetchall()
        print(curaims)

    print("Claims table retrieved successfully.")


if __name__ == "__main__":
    # Test the connection with automatic rollback
    try:
        conn = DBConnection.get_connection()
        
        # This will work even if there's an aborted transaction
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            print("✅ Database connection is working!")
    except Exception as e:
        print(f"❌ Error: {e}")