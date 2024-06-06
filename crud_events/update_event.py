import pymysql
import json
from utils.database import conn, logger


def lambda_handler(event, context):
    body = json.loads(event['body'])
    data = update_event(body)
    if data is None:
        # Handle error case (e.g., log or return specific error message)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error update events."})
        }

    # Success case: include retrieved events in the body
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": data,
        }),
    }

def update_event(event):
    id_event = event.get('id')
    name = event.get('name')
    description = event.get('description')
    start_date = event.get('start_date')
    end_date = event.get('end_date')
    category = event.get('event')
    pictures = event.get('pictures')
    try:
        with conn.cursor() as cursor:
            sql = """UPDATE events SET name=%s,description=%s,start_date=%s,end_date=%s,category=%s,pictures=%s WHERE id =%s"""
            cursor.execute(sql,(name,description,start_date,end_date,category,pictures,id_event))
            return "Update event successfully."
    except pymysql.MySQLError as e:
        logger.error("ERROR: Could not retrieve events.")
        logger.error(e)
        return None  # Indicate error
    finally:
        conn.close()



