import psycopg2
import json
from utils.database import get_db_connection


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
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """DELETE FROM events  WHERE id =%s"""
            cursor.execute(sql,(id_event))
            return "Delete event successfully."
    except psycopg2.Error as e:
        print(e)
        raise RuntimeError("ERROR EN DELETE")
    finally:
        conn.close()



