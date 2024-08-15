import json
import boto3
import psycopg2
import logging
from psycopg2.extras import RealDictCursor
from datetime import datetime, date


headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET'
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

        # Find event by id
        cur.execute("SELECT * FROM events WHERE id = %s", (request_id,))
        event = cur.fetchone()

        if not event:
            return {'statusCode': 404, 'body': json.dumps({"error": "Event not found"}), 'headers': headers}

        return {'statusCode': 200, 'body': json.dumps({"data": event}, default=datetime_serializer),'headers': headers}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)}), 'headers': headers}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()


# ------------CONNECT_DB------------------

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

# ------------FUNCTIONS------------------

# Serializador de tipos de dato datetime
def datetime_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# ------------VALIDATIONS------------------

def validate_connection(conn):
    # check if the connection is successful
    if conn is None:
        return {"statusCode": 500, "body": json.dumps({"error": "Connection to the database failed"}),
                'headers': headers}
    return None


def validate_event_path_params(event):
    if "pathParameters" not in event:
        return {"statusCode": 400, "body": json.dumps({"error": "Path parameters is missing from the request."}),
                'headers': headers}

    if event["pathParameters"] is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Path parameters is null."}), 'headers': headers}

    if "id" not in event["pathParameters"]:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID is missing from the path parameters."}),
                'headers': headers}

    if event["pathParameters"]["id"] is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID is missing from the path parameters."}),
                'headers': headers}

    try:
        event['pathParameters']['id'] = int(event['pathParameters']['id'])
    except ValueError:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID data type is wrong."}), 'headers': headers}

    if event['pathParameters']['id'] <= 0:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID invalid value."}), 'headers': headers}
    return None
