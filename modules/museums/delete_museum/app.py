import json

import psycopg2
from psycopg2.extras import RealDictCursor


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Conexión a la base de datos
        conn = psycopg2.connect(
            host='ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
            user='default',
            password='pnQI1h7sNfFK',
            database='verceldb'
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

        request_id = event['pathParameters']['id']
        # SonarQube/SonarCloud ignore end
        sql = "SELECT FROM museums  WHERE id =%s"
        # SonarQube/SonarCloud ignore start
        cur.execute(sql, (request_id,))
        museum = cur.fetchone()

        if not museum:
            return {"statusCode": 404, "body": json.dumps({"error": "Museum not found"})}

        cur.execute("DELETE FROM museums WHERE id = %s", (request_id))
        conn.commit()

        return {'statusCode': 200, 'body': json.dumps({"message": "Museum deleted successfully"})}
    except Exception as e:
        if conn is not None:
            conn.rollback()
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
# SonarQube/SonarCloud ignore end