import base64
import json
import logging
import uuid
import jwt
import boto3
import re
import psycopg2


headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST'
}


# -------------------LAMBDA----------------------------
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
        title = request_body['title']
        description = request_body['description']
        creation_date = request_body['creation_date']
        technique = request_body['technique']
        artists = request_body['artists']
        id_museum = request_body['id_museum']
        pictures = request_body['pictures']

        # Upload image to S3
        # Get data access to S3
        SECRETS = get_secrets()
        AWS_ACCESS_KEY_ID = SECRETS['AWS_ACCESS_KEY_ID']
        AWS_SECRET_ACCESS_KEY = SECRETS['AWS_SECRET_ACCESS_KEY']
        BUCKET_NAME = SECRETS['BUCKET_NAME']

        # do for loop for multiple images
        client_s3 = get_client_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)

        for i in range(len(pictures)):
            s3_url = upload_image_to_s3(pictures[i - 1], client_s3, BUCKET_NAME)
            logging.info(f"Image uploaded to S3: {s3_url}")
            pictures[i - 1] = s3_url

        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Insert work
        insert_work_query = """
                INSERT INTO works(title, description, creation_date, technique, artists, id_museum, pictures) 
                VALUES (%s,%s,%s,%s,%s,%s,%s)
                """
        cur.execute(insert_work_query, (title, description, creation_date, technique, artists, id_museum, pictures))

        # Commit query
        conn.commit()
        return {'statusCode': 200, 'body': json.dumps({"message": "Work created successfully"}), 'headers': headers}
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


def get_client_s3(access_key, secret_key):
    return boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)


def upload_image_to_s3(base64_data, client_s3, bucket_name):
    binary_data, file_name = get_binary_data_and_name_file_to_upload(base64_data)
    response = client_s3.put_object(Bucket=bucket_name, Key=file_name, Body=binary_data, ContentType='image/*')
    logging.debug(f"File uploaded to S3 {response}")
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
    return s3_url


def get_properties_file_from_base64(base64_data):
    return json.dumps({
        'mime_type': base64_data.split(";")[0].split(":")[1],
        'extension': base64_data.split(";")[0].split(":")[1].split("/")[1],
        'base64_data': base64_data.split(",")[1]
    })


# Function to get binary data and name file to upload

def get_binary_data_and_name_file_to_upload(base64_data):
    properties = get_properties_file_from_base64(base64_data)
    properties = json.loads(properties)
    base64_data = properties['base64_data']
    extension = properties['extension']

    binary_data = base64.b64decode(base64_data)
    file_name = f"images/{uuid.uuid4()}.{extension}"

    return binary_data, file_name


def get_secrets():
    secret_name = "prod/musepa"
    region_name = "us-west-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        logging.info(f"Client to get secret: {client}")
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        logging.debug(f"Secret value response: {get_secret_value_response}")
    except Exception as e:
        logging.exception('Error get_secrets')
        raise e
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)


# ------ AUTHORIZATION--------

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
        return {'statusCode': 403, 'body': json.dumps({"error": "Access denied: insufficient permissions"}),
                "headers": headers}

    return None
 # ----- CONNECT_DB--------

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


#------ VALIDATIONS-------------------

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

    # Check if the event body is not a str
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
    letters_regex = re.compile(r"^[a-zA-Z\s]+$")
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    if "title" not in payload or not isinstance(payload["title"], str) or not letters_regex.match(payload["title"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'title'"}), "headers": headers}

    if "description" not in payload or not isinstance(payload["description"], str) or not letters_regex.match(
            payload["description"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'description'"}),
                "headers": headers}

    if "creation_date" not in payload or not isinstance(payload["creation_date"], str) or not date_regex.match(
            payload["creation_date"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'creation_date'"}),
                "headers": headers}

    if "technique" not in payload or not isinstance(payload["technique"], str) or not letters_regex.match(
            payload["technique"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'technique'"}), "headers": headers}

    if "artists" not in payload or not isinstance(payload["artists"], list) or not all(
            isinstance(artist, str) and letters_regex.match(artist) for artist in payload["artists"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'artists'"}), "headers": headers}

    if "id_museum" not in payload or not isinstance(payload["id_museum"], int):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id_museum'"}), "headers": headers}

    if "pictures" not in payload or not isinstance(payload["pictures"], list) or not all(
            isinstance(picture, str) for picture in payload["pictures"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"}), "headers": headers}

    return None
