import psycopg2
import json
import logging
from crud_events.utils.database import conn

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        data = delete_event(body)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": data,
            }),
        }
    except Exception as e:
        logger.error(f"Error updating events: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error updating events."})
        }



def delete_event(event):
    id_event = event.get('id_event')
    try:
        with conn.cursor() as cursor:
            sql = """DELETE FROM events  WHERE id =%s"""
            cursor.execute(sql,(id_event,))
            conn.commit()
            return "Delete event successfully."
    except psycopg2.Error as e:
        logger.error(f"Error delete event: {e}")
        return "Error delete event."
    finally:
        conn.close()



