import json
from functions import datetime_serializer
from psycopg2.extras import RealDictCursor
from validations import validate_connection
from connect_db import get_db_connection


def lambda_handler(_event, _context):
    conn = None
    cur = None
    try:
       
        # Database connection
        conn = get_db_connection()

        # Validate connection
        valid_conn_res = validate_connection(conn)
        if valid_conn_res is not None:
            return valid_conn_res

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        
        # Find all events
        cur.execute("SELECT * FROM events")
       

        events = cur.fetchall()

        return {'statusCode': 200, 'body': json.dumps({"data": events}, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    
