import json
import logging

import psycopg2

from crud_museums.utils.database import get_db_connection

logger = logging.getLogger()
logger.setLevel(logging.INFO)


# Función de controlador Lambda
def lambda_handler(event, __):
    try:
        body = json.loads(event['body'])
        data = insert_museum(body)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": data,
            }),
        }
    except Exception as e:
        logger.error(f"Error saving museum: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error updating museum."})
        }


# Función para actualizar eventos
def insert_museum(event):
    name = event.get('name')
    location = event.get('location')
    tariffs = event.get('tariffs')
    schedules = event.get('schedules')
    contact_number = event.get('contact_number')
    contact_email = event.get('contact_email')
    id_owner = event.get('id_owner')
    pictures = event.get('pictures')
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """INSERT INTO museums  (name, location, tariffs, schedules, contact_number, contact_email, id_owner, pictures) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"""
            cursor.execute(sql, (name, location, tariffs, schedules, contact_number, contact_email, id_owner, pictures))
            conn.commit()
            return "Insert museum successfully."
    except psycopg2.Error as e:
        logger.error(f"Error updating event: {e}")
        return "Error insert museum."
    finally:
        conn.close()