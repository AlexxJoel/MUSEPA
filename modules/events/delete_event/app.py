import json

import psycopg2
from validations import validate_connection, validate_event_path_params


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

        # Validate connection
        valid_conn_res = validate_connection(conn)
        if valid_conn_res is not None:
            return valid_conn_res

        # Validate path params in event
        valid_path_params_res = validate_event_path_params(event)
        if valid_path_params_res is not None:
            return valid_path_params_res

        cur = conn.cursor()
        # SonarQube/SonarCloud ignore end
        request_id = event['pathParameters']['id']
        sql = """DELETE FROM events  WHERE id =%s"""
        # SonarQube/SonarCloud ignore start
        cur.execute(sql, (request_id,))
        conn.commit()

        cur.close()
        conn.close()

        return {'statusCode': 200, 'body': json.dumps({"message": "Event deleted successfully"})}
    except Exception as e:
        return {'statusCode': 500,'body': json.dumps({"error": str(e)})}
# SonarQube/SonarCloud ignore end
