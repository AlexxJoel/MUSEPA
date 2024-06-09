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
         # select the event by id
        sql = """SELECT * FROM works WHERE id = %s"""

        # # execute the query
        cur.execute(sql, (request_id,))
        row = cur.fetchall()
        cur.close()
        conn.close()
        #
        if len(row) == 0:
            return {
                'statusCode': 404,
                'body': json.dumps({"error": "Work not found"})
            }

        return  {
            'statusCode': 200,
            'body': json.dumps(serialize_rows(row, cur), default=datetime_serializer)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }