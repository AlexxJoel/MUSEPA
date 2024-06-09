import json

import psycopg2


def lambda_handler(event, context):
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

        if not isinstance(event['pathParameters']['id'], int):
            return {"statusCode": 400, "body": json.dumps({"error": "Request ID data type is wrong."})}

        if event['pathParameters']['id'] <= 0:
            return {"statusCode": 400, "body": json.dumps({"error": "Request ID invalid value."})}

        cur = conn.cursor()

        request_id = event['pathParameters']['id']
        # SonarQube/SonarCloud ignore end
        sql = """DELETE FROM works  WHERE id =%s"""
        # SonarQube/SonarCloud ignore start
        cur.execute(sql, (request_id,))
        conn.commit()

        cur.close()
        conn.close()

        return {'statusCode': 200, 'body': json.dumps({"message": "Work deleted successfully"})}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
# SonarQube/SonarCloud ignore end
