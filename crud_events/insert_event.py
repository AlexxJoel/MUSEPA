import psycopg2
import json
from utils.database import get_db_connection


def lambda_handler(event, context):
    body = json.loads(event['body'])
    data = insert_event(body)
    if data is None:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error insert events."}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"message": data})
    }

def insert_event(event):
    name = event.get('name')
    description = event.get('description')
    start_date = event.get('start_date')
    end_date = event.get('end_date')
    category = event.get('event')
    pictures = event.get('pictures')
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = """INSERT INTO events(name,description,start_date,end_date,category,pictures) VALUES (%s,%s,%s,%s,%s,%s)"""
            cursor.execute(sql,(name,description,start_date,end_date,category,pictures))
            conn.commit()
            return "Inserted event successfully."
    except psycopg2.Error as e:
        print(e)
        raise RuntimeError("ERROR EN INSERT")
    finally:
        conn.close()



