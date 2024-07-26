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
    numbers_regex = re.compile(r"^\d+$")

    if "id" not in payload or not isinstance(payload["id"], str) or not numbers_regex.match(payload["id"]):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id'"})}

    if "favorites" not in payload or not isinstance(payload["favorites"], list):
        return {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'favorites'"})}

    return None
