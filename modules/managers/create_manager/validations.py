import json
import re


def validate_connection(conn):
    # check if the connection is successful
    if conn is None:
        return {"statusCode": 500, "body": json.dumps({"error": "Connection to the database failed"})}
    return None


def validate_event_body(event):
    # Check if the event has a body
    if "body" not in event:
        return {"statusCode": 400, "body": json.dumps({"error": "No body provided."})}

    # Check if the event body is not None
    if event["body"] is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Body is null."})}

    # Check if the event body is not a list
    if isinstance(event["body"], list):
        return {"statusCode": 400, "body": json.dumps({"error": "Body can not be a list."})}

    # Check if the event body is not empty
    if not event["body"]:
        return {"statusCode": 400, "body": json.dumps({"error": "Body is empty."})}

    # Try to load the JSON body from the event
    try:
        json.loads(event['body'])
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "The request body is not valid JSON"})}

    return None


def validate_payload(payload):
    letters_regex = re.compile(r"^[a-zA-Z\s\d]+$")
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    phoneNumber_regex = re.compile(r"^\+?[1-9]\d{1,14}|\(\d{1,4}\)\s*\d{1,4}(-|\s)?\d{1,4}$")
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")  # Corregido

    if "email" not in payload or not isinstance(payload["email"], str) or not email_regex.match(payload["email"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'email'"})}

    if "password" not in payload or not isinstance(payload["password"], int):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'password'"})}

    if "username" not in payload or not isinstance(payload["username"], str) or not letters_regex.match(
            payload["username"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'username'"})}

    if "name" not in payload or not isinstance(payload["name"], str) or not letters_regex.match(payload["name"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"})}

    if "surname" not in payload or not isinstance(payload["surname"], str) or not letters_regex.match(
            payload["surname"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'surname'"})}

    if "lastname" not in payload or not isinstance(payload["lastname"], str) or not letters_regex.match(
            payload["lastname"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'lastname'"})}

    if "phone_number" not in payload or not isinstance(payload["phone_number"], str) or not phoneNumber_regex.match(
            payload["phone_number"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'phone_number'"})}

    if "address" not in payload or not isinstance(payload["address"], str) or not letters_regex.match(
            payload["address"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'address'"})}

    if "birthdate" not in payload or not isinstance(payload["birthdate"], str) or not date_regex.match(
            payload["birthdate"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'birthdate'"})}
    return None
