import json
import jwt
import boto3
import psycopg2
import logging
from psycopg2.extras import RealDictCursor
from datetime import datetime, date
import re

headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET'
}


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:

        # Authorizate
        authorization_response = authorizate_user(event)
        if authorization_response is not None:
            return authorization_response

        # Database connection
        conn = get_db_connection()

        # Validate connection
        valid_conn_res = validate_connection(conn)
        if valid_conn_res is not None:
            return valid_conn_res

        # Validate body in event
        valid_body_res = validate_event_body(event)
        if valid_body_res is not None:
            return valid_body_res

        # Validate payload
        request_body = json.loads(event['body'])
        valid_payload_res = validate_payload(request_body)
        if valid_payload_res is not None:
            return valid_payload_res

        # Get values from body
        request_email = request_body['email']

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Find user by email
        sql = "SELECT * FROM users WHERE email = %s LIMIT 1"
        cur.execute(sql, (request_email,))
        user = cur.fetchone()

        if not user:
            return {"statusCode": 404, "body": json.dumps({"error": "User not found"}), "headers": headers}

        # Find visitor by user id
        sql = "SELECT * FROM visitors WHERE id_user = %s"
        cur.execute(sql, (user['id'],))
        visitor = cur.fetchone()

        if not visitor:
            return {"statusCode": 404, "body": json.dumps({"error": "Visitor not found"}), "headers": headers}

        visitor['user'] = user

        return {"statusCode": 200, "body": json.dumps({'data': visitor}, default=datetime_serializer),
                "headers": headers}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)}), "headers": headers}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()


# -------------------AUTHORIZATION-------------------------------

def authorizate_user(_event):
    token = _event['headers']['Authorization'].split(' ')[1]
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    roles = decoded_token.get('cognito:groups')
    role = roles[0]

    if role is None:
        return {'statusCode': 400, 'body': json.dumps({"error": "Role not found in token"}), 'headers': headers}

    if len(roles) <= 0:
        return {'statusCode': 400, 'body': json.dumps({"error": "Role not found in token"}), 'headers': headers}

    return None

# -------------------CONNECT_DB----------------------------------

def get_db_connection():
    secrets = get_secrets()
    host = secrets['POSTGRES_HOST']
    user = 'default'
    password = secrets['POSTGRES_PASSWORD']
    database = secrets['POSTGRES_DATABASE']
    return psycopg2.connect(
        host=host,
        user=user,
        password=password,
        database=database
    )


def get_secrets():
    secret_name = "prod/musepa"
    region_name = "us-west-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        logging.exception('Error get_secrets')
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

# -------------------FUNCTIONS-----------------------------------
# Serializador de tipos de dato datetime
def datetime_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# -------------------VALIDATIONS--------------------------------

def validate_connection(conn):
    # check if the connection is successful
    if conn is None:
        return {"statusCode": 500, "body": json.dumps({"error": "Connection to the database failed"}),
                "headers": headers}
    return None


def validate_event_body(event):
    # Check if the event has a body
    if "body" not in event:
        return {"statusCode": 400, "body": json.dumps({"error": "No body provided."}), "headers": headers}

    # Check if the event body is not None
    if event["body"] is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Body is null."}), "headers": headers}

    # Check if the event body is not a list
    if isinstance(event["body"], list):
        return {"statusCode": 400, "body": json.dumps({"error": "Body can not be a list."}), "headers": headers}

    # Check if the event body is not empty
    if not event["body"]:
        return {"statusCode": 400, "body": json.dumps({"error": "Body is empty."}), "headers": headers}

    # Try to load the JSON body from the event
    try:
        json.loads(event['body'])
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "The request body is not valid JSON"}), "headers": headers}

    return None

def validate_payload(payload):
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    if "email" not in payload or not isinstance(payload["email"], str) or not email_regex.match(payload["email"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'email'"}), "headers": headers}

    return None

if __name__ == '__main__':
    print(lambda_handler({
        "headers": {
            "Authorization": "Bearer eyJraWQiOiJiV01sRE5Lc3RzMW9wQ0RCYzdJSFBncW45eVZURWJKbTFhYVJlXC9NRU0yOD0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiIzOTI5NDllZS0yMGYxLTcwZWEtOThkMi1mNWQ2ZGNhZDhiMmIiLCJjb2duaXRvOmdyb3VwcyI6WyJtYW5hZ2VyIl0sImVtYWlsX3ZlcmlmaWVkIjpmYWxzZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLXdlc3QtMS5hbWF6b25hd3MuY29tXC91cy13ZXN0LTFfZ0dIMTdkSlByIiwiY29nbml0bzp1c2VybmFtZSI6ImFkbWluIiwib3JpZ2luX2p0aSI6IjUxYWQzMTM5LTViMTAtNGVkNy1hNjgyLWYyOGRiYjI3ZWM2ZSIsImF1ZCI6Im1ocHI3ODExcXV1Z3Q5YnVmcm9wc3U1anQiLCJldmVudF9pZCI6IjBmYzgxYjU0LWNkMTctNDQyMy1iNGZlLTk2NWFmYjU5ZmEyNiIsInRva2VuX3VzZSI6ImlkIiwiYXV0aF90aW1lIjoxNzIzNzQ2ODM0LCJleHAiOjE3MjM3NTA0MzQsImlhdCI6MTcyMzc0NjgzNCwianRpIjoiNDYyNTE0YjktMDcyMC00NzQyLWE0YWYtMmUzOWJlZGYwNjU5IiwiZW1haWwiOiJmbG9yZXNzYW50YW5hcGFibG9zYW11ZWxAZ21haWwuY29tIn0.SfbTbfgtM9S1yNGlMrudsAK-n8ZYEQyKfvX61msDwJLAMUXQPPxqMauQ52OuB5qms003LpzaK1kCVsT_AL9gJ7urH_tAuxmw6JQoPfjEfLneEFrp8S5F3EEowtLkwhdo3sP00NeHnmA71cmLSHhZtCohgKw7t5TT0ThHvzemtbIIGTg4dOD5-1sytokzhvxfDW7PEbrQ-ftKp_xuwGJ5Wm_w9Z-FoyUIftZuw4bN-5pE6byF282lr03Z7xug_UxSGsNa9s0IxQzXYbaLHC5K-cjYcHSax4TqXMAnoXqHvcD7kryAcU1jySrCff8jWGVoZDSCukHMnDLP1ojlVsOA6A"
        },
        "body": json.dumps({
            "email": "jose@example.com",
        })
    }, None))