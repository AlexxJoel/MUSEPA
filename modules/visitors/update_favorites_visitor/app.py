import json
from authorization import authorizate_user
from connect_db import get_db_connection
from validations import validate_connection, validate_event_body, validate_payload


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

        # Validate body in event
        valid_event_body_res = validate_event_body(event)
        if valid_event_body_res is not None:
            return valid_event_body_res

        # Validate payload
        request_body = json.loads(event['body'])
        valid_payload_res = validate_payload(request_body)
        if valid_payload_res is not None:
            return valid_payload_res

        
        # Get payload values
        id = request_body["id"]
        favorites = request_body["favorites"]
       
        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Find visitor by id
        cur.execute("SELECT * FROM visitors WHERE id = %s", (id,))
        visitor = cur.fetchone()

        if not visitor:
            return {"statusCode": 404, "body": json.dumps({"error": "Visitor not found"})}

        # Update visitor by visitor_id
        update_visitor_query = """ UPDATE visitors SET favorites = %s WHERE id = %s """
        cur.execute(update_visitor_query, (favorites, id))

        # Commit query
        conn.commit()
        return {"statusCode": 200, "body": json.dumps({"message": "Favorites updated successfully"})}
    except Exception as e:
        # Handle rollback
        if conn is not None:
            conn.rollback()
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    
