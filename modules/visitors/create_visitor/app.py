import json

import psycopg2


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

        

        # start transaction
        conn.autocommit = False

        request_body = json.loads(event['body'])

        email = request_body['email']
        password = request_body['password']
        username = request_body['username']
        id_role = 2
        name = request_body['name']
        surname = request_body['surname']
        lastname = request_body['lastname']

        cur = conn.cursor()

        # insert user
        insert_user_query = """
                INSERT INTO users (email, password, username, id_role)
                VALUES (%s, %s, %s, %s) RETURNING id
                """
        cur.execute(insert_user_query, (email, password, username, id_role))
        id_user = cur.fetchone()[0]

        # insert visitor
        insert_visitor_query = """
                INSERT INTO visitors (name, surname, lastname, id_user)
                VALUES (%s, %s, %s, %s)
                """
        cur.execute(insert_visitor_query, (name, surname, lastname, id_user))

        conn.commit()
        return {
            'statusCode': 200,
            'body': json.dumps("Visitor created successfully")
        }
    except Exception as e:
        if conn is not None:
            conn.rollback()
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
