import json

import psycopg2
from functions import datetime_serializer
from psycopg2.extras import RealDictCursor


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Conexión a la base de datos
        conn = psycopg2.connect(
            host="ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech",
            user="default",
            password="pnQI1h7sNfFK",
            database="verceldb",
        )

        if not conn:
            return {"statusCode": 500, "body": json.dumps({"error": "Failed to connect to the database."})}

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

        cur = conn.cursor(cursor_factory=RealDictCursor)

        request_id = event["pathParameters"]["id"]
# SonarQube/SonarCloud ignore end
        # find visitor by id
        sql = "SELECT * FROM visitors WHERE id = %s"
        # SonarQube/SonarCloud ignore start
        cur.execute(sql, (request_id,))
        visitor = cur.fetchone()

        if not visitor:
            return {"statusCode": 404, "body": json.dumps({"error": "Visitor not found"})}

        # find user
        sql = "SELECT * FROM users WHERE id = %s"
        cur.execute(sql, (visitor["id_user"],))
        user = cur.fetchone()

        visitor['user'] = user

        if len(user) == 0:
            return {"statusCode": 404, "body": json.dumps({"error": "Visitor not found"})}

        return {"statusCode": 200, "body": json.dumps(visitor, default=datetime_serializer)}
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
# SonarQube/SonarCloud ignore end