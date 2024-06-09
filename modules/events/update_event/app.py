import json
import psycopg2
from functions import (datetime_serializer, serialize_rows)


def lambda_handler(event, __):
    try:

        # Conexión a la base de datos
        conn = psycopg2.connect(
            host='ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
            user='default',
            password='pnQI1h7sNfFK',
            database='verceldb'
        )

        # check if the connection is successful
        if conn is None:
            return {
                'statusCode': 500,
                'body': json.dumps("Connection to the database failed")
            }

        # Check if the event has a body
        if 'body' not in event:
            return {
                'statusCode': 400,
                'body': json.dumps("No body provided")
            }

        # Try to load the JSON body from the event
        try:
            request_body = json.loads(event['body'])
        except json.JSONDecodeError:
            return {
                "statusCode": 400,
                "body": json.dumps({"error": "The request body is not valid JSON"})
            }

        # TODO: validate the request body

        request_body = json.loads(event['body'])

        id = request_body['id']
        name = request_body['name']
        description = request_body['description']
        start_date = request_body['start_date']
        end_date = request_body['end_date']
        category = request_body['category']
        pictures = request_body['pictures']
        id_museum = request_body['id_museum']

        cur = conn.cursor()

        # execute the query
        sql = """UPDATE events SET name=%s, description=%s, start_date=%s, end_date=%s, category=%s, pictures=%s, id_museum=%s WHERE id=%s"""
        cur.execute(sql, (name, description, start_date, end_date, category, pictures, id_museum, id))

        conn.commit()

        cur.close()
        conn.close()

        return {
            'statusCode': 200,
            'body': json.dumps({"message": "Event updated successfully yeah!"})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
