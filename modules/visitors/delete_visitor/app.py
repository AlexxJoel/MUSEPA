import json
import psycopg2
from functions import (datetime_serializer, serialize_rows)

def lambda_handler(event, context):
    try:
        # Conexión a la base de datos
        conn = psycopg2.connect(
            host='ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
            user = 'default',
            password = 'pnQI1h7sNfFK',
            database = 'verceldb'
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


        cur = conn.cursor()

        request_id = event['pathParameters']['id']

        # find user by id
        cur.execute("SELECT * FROM museums WHERE id = %s returning id", (request_id,))
        user = cur.fetchone()

        if not user:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Visitor not found"})
            }


        cur.execute("DELETE FROM visitors WHERE id = %s", (request_id,))
        conn.commit()


        cur.close()
        conn.close()

        return  {
            'statusCode': 200,
            'body': json.dumps({"message": "Visitor deleted successfully"})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
