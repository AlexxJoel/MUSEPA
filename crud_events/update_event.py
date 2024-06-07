import json
import logging

import psycopg2

from crud_events.utils.database import get_db_connection

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Función de controlador Lambda
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        data = update_event(body)
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


# Función para actualizar eventos
def update_event(event):
    id_event = event.get('id')
    name = event.get('name')
    description = event.get('description')
    start_date = event.get('start_date')
    end_date = event.get('end_date')
    category = event.get('category')
    pictures = event.get('pictures')
    id_museum = event.get('id_museum')
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """UPDATE events SET name=%s, description=%s, start_date=%s, end_date=%s, category=%s, pictures=%s, id_museum=%s WHERE id=%s"""
            cursor.execute(sql, (name, description, start_date, end_date, category, pictures, id_museum, id_event))
            conn.commit()
            return "Event updated successfully."
    except psycopg2.Error as e:
        logger.error(f"Error updating event: {e}")
        return "Error updating event."
    finally:
        conn.close()
