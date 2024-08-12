import json
import re

headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'POST'
}


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
