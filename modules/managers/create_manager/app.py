import json

from validations import validate_connection, validate_event_body, validate_payload
from connect_db import get_db_connection


def lambda_handler(event, _context):
    cur = None
    conn = None
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
        email = request_body['email']
        password = request_body['password']
        username = request_body['username']
        id_role = 1
        name = request_body['name']
        surname = request_body['surname']
        lastname = request_body['lastname']
        phone_number = request_body['phone_number']
        address = request_body['address']
        birthdate = request_body['birthdate']
        id_museum = request_body['id_museum']
        # SonarQube/SonarCloud ignore start
        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Insert user
        insert_user_query = """
                INSERT INTO users (email, password, username, id_role)
                VALUES (%s, %s, %s, %s) RETURNING id
                """
        cur.execute(insert_user_query, (email, password, username, id_role))
        id_user = cur.fetchone()[0]

        # Insert manager
        insert_manager_query = """
                INSERT INTO managers (name, surname, lastname, phone_number, address, birthdate, id_user, id_museum)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
        cur.execute(insert_manager_query,
                    (name, surname, lastname, phone_number, address, birthdate, id_user, id_museum))

        # Commit query
        conn.commit()
        return {'statusCode': 200, 'body': json.dumps({"message": "Manager created successfully"})}
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
