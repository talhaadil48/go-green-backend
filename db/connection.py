import os
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv
from pathlib import Path

# resolve project root and load .env.local
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = BASE_DIR / ".env.local"

load_dotenv(dotenv_path=ENV_PATH)

class DBConnection:
    _connection = None

    @classmethod
    def get_connection(cls):
        if cls._connection is None or cls._connection.closed:
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
        return cls.get_connection().cursor()

    @classmethod
    def close_connection(cls):
        if cls._connection and not cls._connection.closed:
            cls._connection.close()
            cls._connection = None
            print("Database connection closed.")
