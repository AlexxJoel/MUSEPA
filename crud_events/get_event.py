import psycopg2
import json
from crud_events.utils.database import conn
from crud_events.utils.functions import (datetime_serializer, serialize_rows)


# Función de controlador Lambda
def lambda_handler(event, context):
    try:
        print(event)
        data = get_events()
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Events retrieved successfully.",
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
def get_events():
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM events"
            cursor.execute(sql)
            events = cursor.fetchall()

            return serialize_rows(events, cursor)
    except psycopg2.Error as e:
        print(e)
        raise RuntimeError("ERROR EN GET")
    finally:
        conn.close()
