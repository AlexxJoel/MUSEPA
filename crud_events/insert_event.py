import psycopg2
import json
from crud_events.utils.database import conn
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        data = insert_event(body)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": data
            })
        }
    except Exception as e:
        logger.error(f"Error updating events: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error updating events."})
        }


def insert_event(event):
    name = event.get('name')
    description = event.get('description')
    start_date = event.get('start_date')
    end_date = event.get('end_date')
    category = event.get('category')
    pictures = event.get('pictures')
    id_museum = event.get('id_museum')
    try:
        with conn.cursor() as cursor:
            sql = """INSERT INTO events(name,description,start_date,end_date,category,pictures,id_museum) VALUES (%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(sql,(name,description,start_date,end_date,category,pictures,id_museum))
            conn.commit()
            return "Inserted event successfully."
    except psycopg2.Error as e:
        logger.error(f"Error updating event: {e}")
        return "Error updating event."
    finally:
        conn.close()