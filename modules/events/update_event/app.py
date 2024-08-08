import base64
import json
import logging
import uuid

import boto3

from authorization import authorizate_user
from connect_db import get_db_connection
from validations import validate_connection, validate_event_body, validate_payload

logging.basicConfig(level=logging.INFO)


def lambda_handler(event, _context):
    cur = None
    conn = None
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
        id = request_body['id']
        name = request_body['name']
        description = request_body['description']
        start_date = request_body['start_date']
        end_date = request_body['end_date']
        category = request_body['category']
        pictures = request_body['pictures']
        id_museum = request_body['id_museum']

        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Find event by id
        cur.execute("SELECT id,pictures FROM events WHERE id = %s", (id,))
        result = cur.fetchone()
        logging.info(f"Event found: {result}")

        if not result:
            return {"statusCode": 404, "body": json.dumps({"error": "Event not found"})}

        # Get data access to s3
        # Get data access to S3
        SECRETS = get_secrets()
        AWS_ACCESS_KEY_ID = SECRETS['AWS_ACCESS_KEY_ID']
        AWS_SECRET_ACCESS_KEY = SECRETS['AWS_SECRET_ACCESS_KEY']
        BUCKET_NAME = SECRETS['BUCKET_NAME']

        client_s3 = get_client_s3(AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY )

        # Get pictures to delete from s3
        get_all_pictures = list(set(result[1]) - set(pictures))
        names_images_to_delete = []
        for picture in get_all_pictures:
            names_images_to_delete.append(get_name_from_s3(picture))

        # Delete images from s3
        for picture in names_images_to_delete:
            delete_image_from_s3(client_s3, BUCKET_NAME, picture)

        # Update pictures
        pictures_urls = []
        # Upload new images to s3
        for picture in pictures:
            s3_url = upload_image_to_s3(picture, client_s3, BUCKET_NAME)
            pictures_urls.append(s3_url)

        logging.info(f"Images uploaded to S3: {pictures_urls}")

        # Update event
        sql = """UPDATE events SET name=%s, description=%s, start_date=%s, end_date=%s, category=%s, pictures=%s, id_museum=%s WHERE id=%s"""
        cur.execute(sql, (name, description, start_date, end_date, category, pictures_urls, id_museum, id))

        # Commit query
        conn.commit()
        return {'statusCode': 200, 'body': json.dumps({"message": "Event updated successfully"})}
    except Exception as e:
        # Handle rollback
        if conn is not None:
            conn.rollback()
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()


def get_secrets():
    secret_name = "prod/musepa/vercel/postgres"
    region_name = "us-west-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        logging.info(f"Client to get secret: {client}")
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        logging.debug(f"Secret value response: {get_secret_value_response}")
    except Exception as e:
        raise e
    secret = get_secret_value_response['SecretString']
    return json.loads(secret)


def get_properties_file_from_base64(base64_data):
    return json.dumps({
        'mime_type': base64_data.split(";")[0].split(":")[1],
        'extension': base64_data.split(";")[0].split(":")[1].split("/")[1],
        'base64_data': base64_data.split(",")[1]
    })


def get_binary_data_and_name_file_to_upload(base64_data):
    properties = get_properties_file_from_base64(base64_data)
    properties = json.loads(properties)
    base64_data = properties['base64_data']
    extension = properties['extension']

    binary_data = base64.b64decode(base64_data)
    file_name = f"images/{uuid.uuid4()}.{extension}"

    return binary_data, file_name


def get_client_s3(access_key, secret_key):
    return boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key)


def upload_image_to_s3(base64_data, client_s3, bucket_name):
    binary_data, file_name = get_binary_data_and_name_file_to_upload(base64_data)
    response = client_s3.put_object(Bucket=bucket_name, Key=file_name, Body=binary_data, ContentType='image/*')
    logging.debug(f"File uploaded to S3 {response}")
    s3_url = f"https://{bucket_name}.s3.amazonaws.com/{file_name}"
    return s3_url


def delete_image_from_s3(s3_client, bucket_name, key):
    logging.debug(f"Deleting image from S3 with key: {key}")
    resp_del = s3_client.delete_object(Bucket=bucket_name, Key=key)
    logging.info(f"Image deleted from S3 with key: {resp_del}")
    return None


def get_name_from_s3(url):
    return 'images/' + url.split('/')[-1]


def img_to_base64(img):
    with open(img, "rb") as image:
        return base64.b64encode(image.read())


