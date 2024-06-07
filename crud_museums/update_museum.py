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
        data = update_museum(body)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": data,
            }),
        }
    except Exception as e:
        logger.error(f"Error updating museum: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error updating museum."})
        }


# Función para actualizar eventos
def update_museum(event):
    id_museum = event.get('id')
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
            sql = """UPDATE museums SET name=%s, location=%s, tariffs=%s, schedules=%s, contact_number=%s, contact_email=%s, id_owner=%s, pictures=%s WHERE id=%s"""
            cursor.execute(sql, (name, location, tariffs, schedules, contact_number, contact_email, id_owner, pictures, id_museum))
            conn.commit()
            return "Museum updated successfully."
    except psycopg2.Error as e:
        logger.error(f"Error updating event: {e}")
        return "Error updating museum."
    finally:
        conn.close()