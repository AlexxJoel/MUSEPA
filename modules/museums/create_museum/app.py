import json
import jwt
import boto3
import psycopg2
from datetime import datetime
import re
import logging

headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST'
}


def lambda_handler(event, __):
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
        valid_event_body_res = validate_event_body(event)
        if valid_event_body_res is not None:
            return valid_event_body_res

        # Validate payload
        request_body = json.loads(event['body'])
        valid_payload_res = validate_payload(request_body)
        if valid_payload_res is not None:
            return valid_payload_res

        # Get payload values
        name = request_body['name']
        location = request_body['location']
        tariffs = request_body['tariffs']
        schedules = request_body['schedules']
        contact_number = request_body['contact_number']
        contact_email = request_body['contact_email']
        pictures = request_body['pictures']

        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Insert museum
        sql = """INSERT INTO museums (name, location, tariffs, schedules, contact_number, contact_email, pictures) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
        cur.execute(sql, (name, location, tariffs, schedules, contact_number, contact_email, pictures))

        # Commit query
        conn.commit()

        return {'statusCode': 200, 'body': json.dumps({"message": "Museum created successfully"}), 'headers': headers}
    except Exception as e:
        # Handle rollback
        if conn is not None:
            conn.rollback()
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)}), 'headers': headers}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()

# ------------------------AUTHORIZER------------------------
def authorizate_user(_event):
    token = _event['headers']['Authorization'].split(' ')[1]
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    roles = decoded_token.get('cognito:groups')
    role = roles[0]

    if role is None:
        return {'statusCode': 400, 'body': json.dumps({"error": "Role not found in token"}), "headers": headers}

    if len(roles) <= 0:
        return {'statusCode': 400, 'body': json.dumps({"error": "Role not found in token"}), "headers": headers}

    if role == "visitor":
        return {'statusCode': 403, 'body': json.dumps({"error": "Access denied: insufficient permissions"}),
                "headers": headers}

    return None

# ------------------------CONNECT_DB------------------------

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

# ------------------------FUNCTIONS------------------------
def datetime_serializer(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# ------------------------VALIDATIONS------------------------

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
        return {"statusCode": 400, "body": json.dumps({"error": "The request body is not valid JSON"}),
                "headers": headers}

    return None


def validate_payload(payload):
    letters_regex = re.compile(r"^[a-zA-Z\s\d]+$")
    pay_regex = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")
    numbers_regex = re.compile(r"^\d+$")
    phoneNumber_regex = re.compile(r"^\+?[1-9]\d{1,14}|\(\d{1,4}\)\s*\d{1,4}(-|\s)?\d{1,4}$")
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")  # Corregido
    if "name" not in payload or not isinstance(payload["name"], str) or not letters_regex.match(payload["name"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"}), "headers": headers}

    if "location" not in payload or not isinstance(payload["location"], str) or not letters_regex.match(
            payload["location"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'location'"}), "headers": headers}

    if "tariffs" not in payload or not isinstance(payload["tariffs"], str):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'tariffs'"}), "headers": headers}

    if "schedules" not in payload or not isinstance(payload["schedules"], str) or not payload["schedules"].strip():
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'schedules'"}), "headers": headers}

    if "contact_number" not in payload or not isinstance(payload["contact_number"], str) or not phoneNumber_regex.match(
            payload["contact_number"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_number'"}),
                "headers": headers}

    if "contact_email" not in payload or not isinstance(payload["contact_email"], str) or not email_regex.match(
            payload["contact_email"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_email'"}),
                "headers": headers}

    if "pictures" not in payload or not isinstance(payload["pictures"], str) or not payload["pictures"].strip():
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"}), "headers": headers}

    return None
