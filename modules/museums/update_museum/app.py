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

        if event['body'] is None:
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

        

        request_body = json.loads(event['body'])

        id = request_body['id']
        name = request_body['name']
        location = request_body['location']
        tariffs = request_body['tariffs']
        schedules = request_body['schedules']
        contact_number = request_body['contact_number']
        contact_email = request_body['contact_email']
        id_owner = request_body['id_owner']
        pictures = request_body['pictures']

        cur = conn.cursor()

        conn.autocommit = False

        # execute the query
        sql = """UPDATE museums SET name=%s, location=%s, tariffs=%s, schedules=%s, contact_number=%s, contact_email=%s, id_owner=%s, pictures=%s WHERE id=%s"""
        cur.execute(sql, (name, location, tariffs, schedules, contact_number, contact_email, id_owner, pictures, id))
        conn.commit()
        return {
            'statusCode': 200,
            'body': json.dumps({"message": "Museum updated successfully"})
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