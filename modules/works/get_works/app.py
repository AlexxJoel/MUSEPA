import json

import psycopg2
from psycopg2.extras import RealDictCursor

from functions import datetime_serializer
from modules.works.get_works.connect_db import get_db_connection


def lambda_handler(_event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Database connection
        conn = get_db_connection

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # SonarQube/SonarCloud ignore end
        # Find all works
        cur.execute("SELECT * FROM works")
        # SonarQube/SonarCloud ignore start

        works = cur.fetchall()

        return {'statusCode': 200, 'body': json.dumps({"data": works}, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    # SonarQube/SonarCloud ignore end
