import json

import psycopg2
from functions import datetime_serializer
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

        # Find manager by id
        sql = "SELECT * FROM managers WHERE id = %s"
        cur.execute(sql, (request_id,))
        manager = cur.fetchone()

        if not manager:
            return {"statusCode": 404, "body": json.dumps({"error": "Manager not found"})}

        # Find user by id
        sql = "SELECT * FROM users WHERE id = %s"
        cur.execute(sql, (manager['id_user'],))
        user = cur.fetchone()

        if not user:
            return {'statusCode': 404, 'body': json.dumps({"error": "User not found"})}

        manager['user'] = user

        return {'statusCode': 200, 'body': json.dumps({"data": manager}, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    # SonarQube/SonarCloud ignore end
