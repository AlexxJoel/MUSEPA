import json
import logging

import boto3
from botocore.exceptions import ClientError

from connect_db import get_db_connection, get_secrets
from validations import validate_connection, validate_event_body, validate_payload

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

