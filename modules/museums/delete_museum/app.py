import json

import psycopg2
from psycopg2.extras import RealDictCursor
from validations import validate_connection, validate_event_path_params


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Database connection
        conn = psycopg2.connect(
            host='ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
            user='default',
            password='pnQI1h7sNfFK',
            database='verceldb'
        )

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
    # SonarQube/SonarCloud ignore end
