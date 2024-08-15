import json
import logging
import psycopg2
import boto3
import re
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO)

headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST'
}


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:

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
        email = request_body['email']
        password = request_body['password']
        username = request_body['username']
        id_role = 2
        name = request_body['name']
        surname = request_body['surname']
        lastname = request_body['lastname']

        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Insert user
        insert_user_query = """
                INSERT INTO users (email, password, username, id_role)
                VALUES (%s, %s, %s, %s) RETURNING id
                """

        logging.info(f"Inserting user with email: {email, username, id_role}")
        cur.execute(insert_user_query, (email, password, username, id_role))
        id_user = cur.fetchone()[0]

        # Insert visitor
        insert_visitor_query = """
                INSERT INTO visitors (name, surname, lastname, id_user)
                VALUES (%s, %s, %s, %s)
                """
        cur.execute(insert_visitor_query, (name, surname, lastname, id_user))

        logging.info(f"Inserting visitor with name: {name, surname, lastname, id_user}")

        # Cognito Insert
        return insert_user_pool(conn, username, email, password)
        logging.info(f"Inserting user pool with username: {username, email, password}")

        conn.commit()
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


def insert_user_pool(conn, username, email, password):
    try:
        secrets = get_secrets()
        REGION_NAME = secrets['REGION_NAME']
        USER_POOL_ID = secrets['USER_POOL_ID']
        client = boto3.client('cognito-idp', region_name=REGION_NAME)

        # Create user
        response = client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=username,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {'Name': 'email_verified', 'Value': 'true'}
            ],
            TemporaryPassword=password
        )

        logging.info(f"User {email} created successfully: {response}")

        response = client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=email,
            GroupName='visitor'
        )

        logging.info(f"User {email} added to group 'visitor': {response}")

        conn.commit()
        return {
            'statusCode': 200,
            'body': json.dumps({"message": "User created successfully, verification email sent."}),
            'headers': headers
        }

    except ClientError as e:

        conn.rollback()
        return {
            'statusCode': 400,
            'body': json.dumps({"error": e.response['Error']['Message']}),
            'headers': headers
        }


# -------------------CONNECT_DB--------------------------------

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

# -------------------VALIDATIONS----------------------------

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
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    if "email" not in payload or not isinstance(payload["email"], str) or not email_regex.match(payload["email"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'email'"}), "headers": headers}

    if "password" not in payload or not isinstance(payload["password"], str) or not payload["password"].strip():
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'password'"}), "headers": headers}

    if "username" not in payload or not isinstance(payload["username"], str) or not letters_regex.match(
            payload["username"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'username'"}), "headers": headers}

    if "name" not in payload or not isinstance(payload["name"], str) or not letters_regex.match(payload["name"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"}), "headers": headers}

    if "surname" not in payload or not isinstance(payload["surname"], str) or not letters_regex.match(
            payload["surname"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'surname'"}), "headers": headers}

    if "lastname" not in payload or not isinstance(payload["lastname"], str) or not letters_regex.match(
            payload["lastname"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'lastname'"}), "headers": headers}
    return None