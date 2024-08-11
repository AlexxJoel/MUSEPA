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

    # Check if the event body is not empty
    if not event["body"]:
        return {"statusCode": 400, "body": json.dumps({"error": "Body is empty."}), "headers": headers}

    # Check if the event body is not a list
    if isinstance(event["body"], list):
        return {"statusCode": 400, "body": json.dumps({"error": "Body can not be a list."}), "headers": headers}

    # Try to load the JSON body from the event
    try:
        json.loads(event['body'])
    except json.JSONDecodeError:
        return {"statusCode": 400, "body": json.dumps({"error": "The request body is not valid JSON"}),
                "headers": headers}

    return None


def validate_payload(payload):
    letters_regex = re.compile(r"^[a-zA-Z\s]+$")
    pay_regex = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")
    numbers_regex = re.compile(r"^\d+$")
    phoneNumber_regex = re.compile(r"^\+?[1-9]\d{1,14}|\(\d{1,4}\)\s*\d{1,4}(-|\s)?\d{1,4}$")
    if "name" not in payload or not isinstance(payload["name"], str) or not letters_regex.match(payload["name"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"}), "headers": headers}

    if "location" not in payload or not isinstance(payload["location"], str) or not letters_regex.match(
            payload["location"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'location'"}), "headers": headers}

    if "tariffs" not in payload or not isinstance(payload["tariffs"], str) or not pay_regex.match(payload["tariffs"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'tariffs'"}), "headers": headers}

    if "schedules" not in payload or not isinstance(payload["schedules"], str) or not payload["schedules"].strip():
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'schedules'"}), "headers": headers}

    if "contact_number" not in payload or not isinstance(payload["contact_number"], str) or not phoneNumber_regex.match(
            payload["contact_number"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_number'"}),
                "headers": headers}

    if "contact_email" not in payload or not isinstance(payload["contact_email"], str) or not email_regex.match(
            payload["contact_email"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_email'"}),
                "headers": headers}

    if "pictures" not in payload or not isinstance(payload["pictures"], str) or not payload["pictures"].strip():
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"}), "headers": headers}

    return None
