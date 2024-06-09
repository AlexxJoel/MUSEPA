import json

import psycopg2
from functions import datetime_serializer
from psycopg2.extras import RealDictCursor


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Conexión a la base de datos
        conn = psycopg2.connect(
            host='ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
            user='default',
            password='pnQI1h7sNfFK',
            database='verceldb'
        )

        if not conn:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to connect to the database"})
            }

        if event['pathParameters'] is None or 'id' not in event['pathParameters']:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Request ID is missing from the request body"})
            }

        cur = conn.cursor(cursor_factory=RealDictCursor)

        request_id = event['pathParameters']['id']
        
        # find visitor by id
        sql = "SELECT * FROM managers WHERE id = %s"
        # SonarQube/SonarCloud ignore start
        cur.execute(sql, (request_id,))
        manager = cur.fetchone()

        if not manager:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Manager not found"})
            }
# SonarQube/SonarCloud ignore end
        # find user
        sql = "SELECT * FROM users WHERE id = %s"
        # SonarQube/SonarCloud ignore start
        cur.execute(sql, (manager['id_user'],))
        user = cur.fetchone()

        manager['user'] = user

        if len(user) == 0:
            return {
                'statusCode': 404,
                'body': json.dumps({"error": "Manager not found"})
            }

        return {
            'statusCode': 200,
            'body': json.dumps(manager, default=datetime_serializer)
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
# SonarQube/SonarCloud ignore end