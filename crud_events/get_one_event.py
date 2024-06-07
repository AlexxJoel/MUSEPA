import psycopg2
import json
from crud_events.utils.database import conn
from crud_events.utils.functions import (datetime_serializer, serialize_row)


# Función de controlador Lambda
def lambda_handler(event, context):
    try:
        body = json.loads(event['body'])
        data = get_one_events(body)
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Event get successfully.",
                "data": data
            }, default=datetime_serializer)
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error retrieving events: {e}"})
        }


# Función para obtener eventos
def get_one_events(event):
    try:
        id_event = event.get('id_event')
        with conn.cursor() as cursor:
            sql = """SELECT id, name, description, start_date, end_date FROM events WHERE id = %s"""  # Selecciona varias columnas
            cursor.execute(sql,(id_event,))
            row = cursor.fetchone()  # Debería devolver un diccionario o una lista

            return serialize_row(row, cursor)  # Usa tu lógica de serialización
    except psycopg2.Error as e:
        print(e)
        raise RuntimeError("ERROR EN GET")
    finally:
        conn.close()
