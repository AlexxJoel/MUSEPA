import json

from psycopg2.extras import RealDictCursor
from validations import validate_connection, validate_event_path_params
from connect_db import get_db_connection
from authorization import authorizate_user


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

        # Start transaction
        conn.autocommit = False

        # Find museum by id
        cur.execute("SELECT id FROM museums WHERE id = %s", (request_id,))
        result = cur.fetchone()

        if not result:
            return {"statusCode": 400, "body": json.dumps({"error": "Museum not found"})}

        # Delete museum
        cur.execute("DELETE FROM museums WHERE id = %s", (request_id,))

        # Commit query
        conn.commit()
        return {'statusCode': 200, 'body': json.dumps({"message": "Museum deleted successfully"})}
    except Exception as e:
        # Handle rollback
        if conn is not None:
            conn.rollback()
        return {'statusCode': 500, 'body': json.dumps({"message": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    
