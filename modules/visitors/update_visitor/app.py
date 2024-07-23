import json

import psycopg2

from validations import validate_connection, validate_event_body, validate_payload
from modules.visitors.update_visitor.connect_db import get_db_connection


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Database connection
        conn = get_db_connection

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

        # SonarQube/SonarCloud ignore end
        # Get payload values
        id = request_body["id"]
        email = request_body["email"]
        password = request_body["password"]
        username = request_body["username"]
        name = request_body["name"]
        surname = request_body["surname"]
        lastname = request_body["lastname"]
        # SonarQube/SonarCloud ignore start
        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Find visitor by id
        cur.execute("SELECT id_user FROM visitors WHERE id = %s", (id,))
        result = cur.fetchone()

        if not result:
            return {"statusCode": 404, "body": json.dumps({"error": "Visitor not found"})}

        user_id = result[0]

        # Update user by user_id
        update_user_query = """ UPDATE users SET email = %s, password = %s, username = %s WHERE id = %s """
        cur.execute(update_user_query, (email, password, username, user_id))

        # Update visitor by visitor_id
        update_visitor_query = """ UPDATE visitors SET name = %s, surname = %s, lastname = %s  WHERE id = %s """
        cur.execute(update_visitor_query, (name, surname, lastname, id))

        # Commit query
        conn.commit()
        return {"statusCode": 200, "body": json.dumps({"message": "Visitor updated successfully"})}
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
    # SonarQube/SonarCloud ignore end
