import json
from psycopg2.extras import RealDictCursor
from authorization import authorizate_user
from connect_db import get_db_connection
from functions import datetime_serializer
from validations import validate_connection


def lambda_handler(_event, _context):
    conn = None
    cur = None
    try:
       
        # Authorizate
        authorization_response = authorizate_user(_event)
        if authorization_response is not None:
            return authorization_response

        # Database connection
        conn = get_db_connection()

        # Validate connection
        valid_conn_res = validate_connection(conn)
        if valid_conn_res is not None:
            return valid_conn_res

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        
        # Find all users
        cur.execute("SELECT * FROM users")
       

        users = cur.fetchall()

        # Find all visitors by user_id
        rows = []
        for user in users:
            cur.execute("SELECT * FROM visitors WHERE id_user = %s", (user["id"],))
            visitor = cur.fetchone()
            if visitor is not None:
                visitor["user"] = user
                rows.append(visitor)

        return {"statusCode": 200, "body": json.dumps({"data": rows}, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    
