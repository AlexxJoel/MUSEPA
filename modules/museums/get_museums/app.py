import json

from psycopg2.extras import RealDictCursor

from connect_db import get_db_connection
from functions import datetime_serializer


def lambda_handler(_event, _context):
    conn = None
    cur = None
    try:
       
        # Database connection
        conn = get_db_connection()

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        
        # Find all managers
        cur.execute("SELECT * FROM museums")
       

        museums = cur.fetchall()

        return {'statusCode': 200, 'body': json.dumps({"data": museums}, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    
