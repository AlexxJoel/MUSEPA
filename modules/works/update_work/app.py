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
        title = request_body['title']
        description = request_body['description']
        creation_date = request_body['creation_date']
        technique = request_body['technique']
        artists = request_body['artists']
        id_museum = request_body['id_museum']
        pictures = request_body['pictures']

        cur = conn.cursor()

        # execute the query
        sql = """UPDATE works SET title=%s, description=%s, creation_date=%s, technique=%s, artists=%s, id_museum=%s, pictures=%s WHERE id=%s"""
        cur.execute(sql, (title, description, creation_date, technique, artists, id_museum, pictures, id))

        conn.commit()

        cur.close()
        conn.close()

        return {
            'statusCode': 200,
            'body': json.dumps({"message": "Work updated successfully"})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
