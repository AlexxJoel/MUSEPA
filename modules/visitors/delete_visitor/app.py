import json
import boto3
import jwt
import psycopg2
import logging
from botocore.exceptions import ClientError
from psycopg2.extras import RealDictCursor

headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'DELETE'
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

        # Validate path params in event
        valid_path_params_res = validate_event_path_params(event)
        if valid_path_params_res is not None:
            return valid_path_params_res

        # Get values from path params
        request_id = event['pathParameters']['id']

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Start transaction
        conn.autocommit = False

        # Find visitor by id
        cur.execute("SELECT * FROM visitors WHERE id = %s", (request_id,))
        visitor = cur.fetchone()

        if not visitor:
            return {"statusCode": 404, "body": json.dumps({"error": "Visitor not found"}), "headers": headers}

        # Delete visitor
        cur.execute("DELETE FROM visitors WHERE id = %s", (request_id,))

        # Delete related user
        cur.execute("DELETE FROM users WHERE id = %s  RETURNING username", (visitor['id_user'],))
        user = cur.fetchone()
        username = user["username"]

        # get secret
        secrets = get_secrets()
        USER_POOL_ID = secrets['USER_POOL_ID']

        # Cognito Integration
        try:
            # CREDENTIALS
            client = boto3.client('cognito-idp', region_name='us-west-1')

            client.admin_delete_user(
                UserPoolId=USER_POOL_ID,
                Username=username
            )

            conn.commit()

            return {"statusCode": 200, "body": json.dumps({"message": "Visitor deleted successfully"}),
                    "headers": headers}

        except ClientError as e:
            # Handle rollback
            conn.rollback()
            return {'statusCode': 400, 'body': json.dumps({"error": e.response['Error']['Message']}),
                    "headers": headers}

    except Exception as e:
        # Handle rollback
        if conn is not None:
            conn.rollback()
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)}), "headers": headers}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()

# -------------------AUTHORIZATION----------------------------

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

# -------------------CONNECT_DB----------------------------

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
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except Exception as e:
        logging.exception('Error get_secrets')
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)
# -------------------VALIDATIONS----------------------------

def validate_connection(conn):
    # check if the connection is successful
    if conn is None:
        return {"statusCode": 500, "body": json.dumps({"error": "Connection to the database failed"}), "headers": {}}
    return None


def validate_event_path_params(event):
    if "pathParameters" not in event:
        return {"statusCode": 400, "body": json.dumps({"error": "Path parameters is missing from the request."}),
                "headers": headers}

    if event["pathParameters"] is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Path parameters is null."}), "headers": headers}

    if "id" not in event["pathParameters"]:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID is missing from the path parameters."}),
                "headers": headers}

    if event["pathParameters"]["id"] is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID is missing from the path parameters."}),
                "headers": headers}

    try:
        event['pathParameters']['id'] = int(event['pathParameters']['id'])
    except ValueError:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID data type is wrong."}), "headers": headers}

    if event['pathParameters']['id'] <= 0:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID invalid value."}), "headers": headers}
    return None

