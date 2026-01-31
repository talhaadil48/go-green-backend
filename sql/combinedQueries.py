from psycopg2.extras import RealDictCursor
from datetime import datetime, timezone
from typing import Optional
from sql.queries import ClaimFormQueries

class Queries(ClaimFormQueries):
    def __init__(self, conn):
       ClaimFormQueries.__init__(self, conn)