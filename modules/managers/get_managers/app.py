import json
import jwt
import boto3
import psycopg2
import logging
from datetime import datetime, date
from psycopg2.extras import RealDictCursor


headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET'
}
def lambda_handler(_event, _context):
    conn = None
    cur = None
    try:
       
        # Authorizate
        authorization_response = authorizate_user(_event)
        if authorization_response is not None:
            return authorization_response

        # Database connection
        conn = get_db_connection()

        # Validate connection
        valid_conn_res = validate_connection(conn)
        if valid_conn_res is not None:
            return valid_conn_res

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        
        # Find all users
        cur.execute("SELECT * FROM managers")
       

        managers = cur.fetchall()

        # Find all managers by id_user
        rows = []
        for manager in managers:
            cur.execute("SELECT * FROM users WHERE id = %s", (manager["id_user"],))
            user = cur.fetchone()
            if user is not None:
                manager["user"] = user
                rows.append(manager)

        return {"statusCode": 200, "body": json.dumps({"data": rows}, default=datetime_serializer), "headers": headers}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)}), "headers": headers}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    

# ------------------------AUTHORIZER------------------------
def authorizate_user(_event):
    token = _event['headers']['Authorization'].split(' ')[1]
    decoded_token = jwt.decode(token, key="secret", algorithms="HS256")
    roles = decoded_token.get('cognito:groups')
    role = roles[0]

    if role is None:
        return {'statusCode': 400, 'body': json.dumps({"error": "Role not found in token"}), "headers": headers}

    if len(roles) <= 0:
        return {'statusCode': 400, 'body': json.dumps({"error": "Role not found in token"}), "headers": headers}

    if role == "visitor":
        return {'statusCode': 403, 'body': json.dumps({"error": "Access denied: insufficient permissions"}), "headers": headers}

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

# Serializador de tipos de dato datetime
def datetime_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")

# ------------------- VALIDATIONS ---------------------------
def validate_connection(conn):
    # check if the connection is successful
    if conn is None:
        return {"statusCode": 500, "body": json.dumps({"error": "Connection to the database failed"}), "headers": headers}
    return None