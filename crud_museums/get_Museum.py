import psycopg2
import json
from crud_museums.utils.database import conn
from crud_museums.utils.functions import (datetime_serializer, serialize_rows)


def lambda_handler(museum, __):
    try:
        print(museum)
        data = get_museums()
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Museums retrieved successfully.",
                "data": data
            }, default=datetime_serializer)
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"message": f"Error retrieving events: {e}"})
        }





def get_museums():
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM museums"
            cursor.execute(sql)
            events = cursor.fetchall()

            return serialize_rows(events, cursor)
    except psycopg2.Error as e:
        print(e)
        raise RuntimeError("ERROR EN GET")
    finally:
        conn.close()