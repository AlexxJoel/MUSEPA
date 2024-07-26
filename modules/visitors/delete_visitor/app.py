import json

import psycopg2
from psycopg2.extras import RealDictCursor

from validations import validate_connection, validate_event_path_params
from modules.visitors.delete_visitor.connect_db import get_db_connection


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

        # Validate path params in event
        valid_path_params_res = validate_event_path_params(event)
        if valid_path_params_res is not None:
            return valid_path_params_res

        # SonarQube/SonarCloud ignore end
        # Get values from path params
        request_id = event['pathParameters']['id']
        # SonarQube/SonarCloud ignore start
        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Start transaction
        conn.autocommit = False

        # Find visitor by id
        cur.execute("SELECT * FROM visitors WHERE id = %s", (request_id,))
        visitor = cur.fetchone()

        if not visitor:
            return {"statusCode": 404, "body": json.dumps({"error": "Visitor not found"})}

        # Delete visitor
        cur.execute("DELETE FROM visitors WHERE id = %s", (request_id,))

        # Delete related user
        cur.execute("DELETE FROM users WHERE id = %s", (visitor['id_user'],))

        # Commit query
        conn.commit()
        return {'statusCode': 200, 'body': json.dumps({"message": "Visitor deleted successfully"})}
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
