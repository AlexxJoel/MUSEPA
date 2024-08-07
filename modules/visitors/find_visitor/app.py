import json

from psycopg2.extras import RealDictCursor
from authorization import authorizate_user
from connect_db import get_db_connection
from functions import datetime_serializer
from validations import validate_connection, validate_event_path_params


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:
       
        # Authorizate
        authorization_response = authorizate_user(event)
        if authorization_response is not None:
            return authorization_response

        # Database connection
        conn = get_db_connection()

        # Validate connection
        valid_conn_res = validate_connection(conn)
        if valid_conn_res is not None:
            return valid_conn_res

        # Validate path params in event
        valid_path_params_res = validate_event_path_params(event)
        if valid_path_params_res is not None:
            return valid_path_params_res

        
        # Get values from path params
        request_id = event['pathParameters']['id']
       
        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Find visitor by id
        sql = "SELECT * FROM visitors WHERE id = %s"
        cur.execute(sql, (request_id,))
        visitor = cur.fetchone()

        if not visitor:
            return {"statusCode": 404, "body": json.dumps({"error": "Visitor not found"})}

        # Find user by id
        sql = "SELECT * FROM users WHERE id = %s"
        cur.execute(sql, (visitor["id_user"],))
        user = cur.fetchone()

        if not user:
            return {"statusCode": 404, "body": json.dumps({"error": "User not found"})}

        visitor['user'] = user

        return {"statusCode": 200, "body": json.dumps({'data': visitor}, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    