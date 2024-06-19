import json

import psycopg2
from .validations import validate_connection, validate_event_body, validate_payload
from .connect_db import connect_database, close_connection


def lambda_handler(event, _context):
    cur = None
    conn = None
    try:
        # SonarQube/SonarCloud ignore start
        # Database connection
        host = 'ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
        user = 'default',
        password = 'pnQI1h7sNfFK',
        database = 'verceldb'

        conn = connect_database(host, user, password, database)

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
        name = request_body['name']
        description = request_body['description']
        start_date = request_body['start_date']
        end_date = request_body['end_date']
        category = request_body['category']
        pictures = request_body['pictures']
        id_museum = request_body['id_museum']
        # SonarQube/SonarCloud ignore start
        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Insert event
        sql = """INSERT INTO events(name,description,start_date,end_date,category,pictures,id_museum) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
        cur.execute(sql, (name, description, start_date, end_date, category, pictures, id_museum))
        connect_database(True)
        # Commit query
        conn.commit()
        return {'statusCode': 200, 'body': json.dumps({"message": "Event created successfully"})}
    except Exception as e:
        # Handle rollback
        if conn is not None:
            conn.rollback()
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            close_connection(conn)
        if cur is not None:
            cur.close()
    # SonarQube/SonarCloud ignore end
