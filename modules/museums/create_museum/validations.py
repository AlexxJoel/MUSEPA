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
    pay_regex = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")
    numbers_regex = re.compile(r"^\d+$")
    phoneNumber_regex = re.compile(r"^\+?[1-9]\d{1,14}|\(\d{1,4}\)\s*\d{1,4}(-|\s)?\d{1,4}$")
    email_regex = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")  # Corregido
    if "name" not in payload or not isinstance(payload["name"], str) or not letters_regex.match(payload["name"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"})}

    if "location" not in payload or not isinstance(payload["location"], str) or not letters_regex.match(
            payload["location"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'location'"})}

    if "tariffs" not in payload or not isinstance(payload["tariffs"], str):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'tariffs'"})}

    if "schedules" not in payload or not isinstance(payload["schedules"], str) or not payload["schedules"].strip():
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'schedules'"})}

    if "contact_number" not in payload or not isinstance(payload["contact_number"], str) or not phoneNumber_regex.match(
            payload["contact_number"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_number'"})}

    if "contact_email" not in payload or not isinstance(payload["contact_email"], str) or not email_regex.match(
            payload["contact_email"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_email'"})}

    if "pictures" not in payload or not isinstance(payload["pictures"], str) or not payload["pictures"].strip():
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"})}

    return None
