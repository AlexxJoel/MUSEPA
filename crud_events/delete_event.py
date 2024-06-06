import pymysql
import json
from utils.database import conn, logger


def lambda_handler(event, context):
    body = json.loads(event['body'])
    data = delete_event(body)
    if data is None:
        # Handle error case (e.g., log or return specific error message)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error delete events."})
        }

    # Success case: include retrieved events in the body
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": data,
        }),
    }

def delete_event(event):
    id_event = event.get('id')
    try:
        with conn.cursor() as cursor:
            sql = """DELETE FROM events  WHERE id =%s"""
            cursor.execute(sql,(id_event))
            return "Delete event successfully."
    except pymysql.MySQLError as e:
        logger.error("ERROR: Could not retrieve events.")
        logger.error(e)
        return None  # Indicate error
    finally:
        conn.close()



