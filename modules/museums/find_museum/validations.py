import json


def validate_connection(conn):
    # check if the connection is successful
    if conn is None:
        return {"statusCode": 500, "body": json.dumps({"error": "Connection to the database failed"})}
    return None


def validate_event_path_params(event):
    if "pathParameters" not in event:
        return {"statusCode": 400, "body": json.dumps({"error": "Path parameters is missing from the request."})}

    if not event["pathParameters"]:
        return {"statusCode": 400, "body": json.dumps({"error": "Path parameters is null."})}

    if "id" not in event["pathParameters"]:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID is missing from the path parameters."})}

    if event["pathParameters"]["id"] is None:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID is missing from the path parameters."})}

    try:
        event['pathParameters']['id'] = int(event['pathParameters']['id'])
    except ValueError:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID data type is wrong."})}

    if event['pathParameters']['id'] <= 0:
        return {"statusCode": 400, "body": json.dumps({"error": "Request ID invalid value."})}
    return None
