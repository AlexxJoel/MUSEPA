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

    # Check if the event body is not a str
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
    letters_regex = re.compile(r"^[a-zA-Z\s]+$")
    numbers_regex = re.compile(r"^\d+$")
    date_regex = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    if "title" not in payload or not isinstance(payload["title"], str) or not letters_regex.match(payload["title"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'title'"})}

    if "description" not in payload or not isinstance(payload["description"], str) or not letters_regex.match(
            payload["description"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'description'"})}

    if "creation_date" not in payload or not isinstance(payload["creation_date"], str) or not date_regex.match(
            payload["creation_date"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'creation_date'"})}

    if "technique" not in payload or not isinstance(payload["technique"], str) or not letters_regex.match(
            payload["technique"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'technique'"})}

    if "artists" not in payload or not isinstance(payload["artists"], str) or not letters_regex.match(
            payload["artists"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'artists'"})}

    if "id_museum" not in payload or not isinstance(payload["id_museum"], str) or not numbers_regex.match(
            payload["id_museum"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id_museum'"})}

    if "pictures" not in payload or not isinstance(payload["pictures"], str) or not payload["pictures"].strip():
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"})}

    return None
