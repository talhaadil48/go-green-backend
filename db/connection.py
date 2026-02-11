import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from pathlib import Path

# Resolve project root and load .env.local
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env.local"
load_dotenv(dotenv_path=ENV_PATH)


class DBConnection:
    _connection = None

    @classmethod
    def get_connection(cls):
        """
        Returns a live database connection.
        Automatically reconnects if the connection is closed.
        """
        # Check if connection exists and is open
        if cls._connection is None or cls._connection.closed != 0:
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

        return cls._connection

    @classmethod
    def get_cursor(cls):
        """
        Returns a cursor from a live connection.
        Always ensures connection is active.
        Use as a context manager:
        
        with DBConnection.get_cursor() as cur:
            cur.execute(...)
        """
        return cls.get_connection().cursor()

    @classmethod
    def close_connection(cls):
        """
        Closes the database connection if open.
        """
        if cls._connection and cls._connection.closed == 0:
            cls._connection.close()
            cls._connection = None
            print("Database connection closed.")
