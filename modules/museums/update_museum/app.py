import json

import psycopg2
from validations import validate_connection, validate_event_body, validate_payload
from modules.museums.update_museum.connect_db import get_db_connection


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
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

        # SonarQube/SonarCloud ignore end
        # Get payload values
        id = request_body['id']
        name = request_body['name']
        location = request_body['location']
        tariffs = request_body['tariffs']
        schedules = request_body['schedules']
        contact_number = request_body['contact_number']
        contact_email = request_body['contact_email']
        pictures = request_body['pictures']
        # SonarQube/SonarCloud ignore start
        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Find museum by id
        cur.execute("SELECT id FROM museums WHERE id = %s", (id,))
        result = cur.fetchone()

        if not result:
            return {"statusCode": 400, "body": json.dumps({"error": "Museum not found"})}

        # Update museum
        update_museum_query = """UPDATE museums SET name=%s, location=%s, tariffs=%s, schedules=%s, contact_number=%s, contact_email=%s, pictures=%s WHERE id=%s"""
        cur.execute(update_museum_query,
                    (name, location, tariffs, schedules, contact_number, contact_email, pictures, id))

        # Commit query
        conn.commit()
        return {'statusCode': 200, 'body': json.dumps({"message": "Museum updated successfully"})}
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
