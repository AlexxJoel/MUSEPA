import json
import jwt
import boto3
from botocore.exceptions import ClientError
import psycopg2
import re

headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'PUT'
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
        valid_event_body_res = validate_event_body(event)
        if valid_event_body_res is not None:
            return valid_event_body_res

        # Validate payload
        request_body = json.loads(event['body'])
        valid_payload_res = validate_payload(request_body)
        if valid_payload_res is not None:
            return valid_payload_res

        # Get payload values
        id = request_body['id']
        email = request_body['email']
        password = request_body['password']
        username = request_body['username']
        name = request_body['name']
        surname = request_body['surname']
        lastname = request_body['lastname']
        phone_number = request_body['phone_number']
        address = request_body['address']
        birthdate = request_body['birthdate']
        id_museum = request_body['id_museum']

        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Find manager by id_user
        cur.execute("SELECT id_user FROM managers WHERE id = %s", (id,))
        result = cur.fetchone()

        if not result:
            return {"statusCode": 404, "body": json.dumps({"error": "Manager not found"}), "headers": headers}

        user_id = result[0]

        # Update user by user_id
        update_user_query = """UPDATE users SET email = %s, password = %s, username = %s WHERE id = %s """
        cur.execute(update_user_query, (email, password, username, user_id))

        # Update manager by manager_id
        update_manager_query = """ UPDATE managers SET name = %s, surname = %s, lastname = %s, phone_number = %s, address = %s, birthdate = %s, id_museum = %s  WHERE id = %s """
        cur.execute(update_manager_query, (name, surname, lastname, phone_number, address, birthdate, id_museum, id))

        # Cognito Integration
        try:
            # Se colocan las credenciales que obtuvimos al generar lo de cognito
            # Configura el cliente de cognito
            client = boto3.client('cognito-idp', region_name='us-west-1')
            user_pool_id = "us-west-1_3onWfQPhK"

            # Eliminar el usuario actual
            client.admin_delete_user(
                UserPoolId=user_pool_id,
                Username=username
            )

            # Crear un nuevo usuario con el nuevo username
            client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=username,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {"Name": 'email_verified', 'Value': 'false'}
                ],
                TemporaryPassword=password
            )

            # Marcar la contraseña temporal como cambiada en Cognito
            client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=username,
                Password=password,
                Permanent=True
            )

            client.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=username,
                GroupName="manager"
            )

            # Commit query
            conn.commit()

            # Si Cognito es exitoso, retorna la respuesta
            return {
                'statusCode': 200,
                'body': json.dumps({"message": "Manager updated successfully."}),
                "headers": headers
            }

        except ClientError as e:
            # Si Cognito falla, realiza rollback de la base de datos
            conn.rollback()
            return {
                'statusCode': 400,
                'body': json.dumps({"error": e.response['Error']['Message']}),
                "headers": headers
            }

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
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)

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
    letters_regex = re.compile(r"[a-zA-Z\s\d]+$")
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    phoneNumber_regex = re.compile(r"^\+?[1-9]\d{1,14}|\(\d{1,4}\)\s*\d{1,4}(-|\s)?\d{1,4}$")
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
    numbers_regex = re.compile(r"^\d+$")

    if "id" not in payload or not isinstance(payload["id"], int):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id'"}), "headers": headers}

    if "email" not in payload or not isinstance(payload["email"], str) or not email_regex.match(payload["email"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'email'"}), "headers": headers}

    if "password" not in payload or not isinstance(payload["password"], str):
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

    if "phone_number" not in payload or not isinstance(payload["phone_number"], str) or not phoneNumber_regex.match(
            payload["phone_number"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'phone_number'"}),
                "headers": headers}

    if "address" not in payload or not isinstance(payload["address"], str) or not letters_regex.match(
            payload["address"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'address'"}), "headers": headers}

    if "birthdate" not in payload or not isinstance(payload["birthdate"], str) or not date_regex.match(
            payload["birthdate"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'birthdate'"}), "headers": headers}

    if "id_museum" not in payload or not isinstance(payload["id_museum"], str) or not numbers_regex.match(
            payload["id_museum"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id_museum'"}), "headers": headers}

    return None
