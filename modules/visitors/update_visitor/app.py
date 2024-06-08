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

        # todo: validate the request body

        request_body = json.loads(event['body'])

        id = request_body['id']
        email = request_body['email']
        password = request_body['password']
        username = request_body['username']
        name = request_body['name']
        surname = request_body['surname']
        lastname = request_body['lastname']

        cur = conn.cursor()

        # start transaction
        conn.autocommit = False

        cur.execute("SELECT id_user FROM visitors WHERE id = %s", (id,))
        result = cur.fetchone()
        if not result:
            print("Visitante no encontrado")
            return
        user_id = result[0]

        # Actualizar el usuario en la tabla users
        update_user_query = """ UPDATE users SET email = %s, password = %s, username = %s WHERE id = %s """
        cur.execute(update_user_query, (
            email,
            password,
            username,
            user_id
        ))

        # Actualizar el visitante en la tabla visitors usando el visitor_id
        update_visitor_query = """ UPDATE visitors SET name = %s, surname = %s, lastname = %s  WHERE id = %s """
        cur.execute(update_visitor_query, (
            name,
            surname,
            lastname,
            id
        ))

        conn.commit()

        cur.close()
        conn.close()

        return {
            'statusCode': 200,
            'body': json.dumps({"message": "Visitor updated successfully"})
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
