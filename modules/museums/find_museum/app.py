import json
import psycopg2
from functions import datetime_serializer
from psycopg2.extras import RealDictCursor

def lambda_handler(event, _context):
    conn = None
    cur = None
    try:

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
         # select the event by id
        sql = "SELECT * FROM museums WHERE id = %s"

        # # execute the query
        cur.execute(sql, (request_id,))
        museum = cur.fetchone()

        if not museum:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "Museum not found"})
            }
        sql = "SELECT * FROM managers WHERE id = %s"
        cur.execute(sql, (museum['id_owner'],))
        manager = cur.fetchone()

        museum['manager'] = manager

        if len(manager) == 0:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Owner not found"})
            }

        return {
            "statusCode": 200,
            "body": json.dumps(museum, default=datetime_serializer)
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
