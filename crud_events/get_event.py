import psycopg2
import json
import os


# Función para obtener la conexión a la base de dato
# Función para obtener eventos


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
            })
        }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error retrieving events."})
        }

def get_events():
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            sql = "SELECT * FROM events"
            cursor.execute(sql)
            return cursor.fetchall()
    except psycopg2.Error as e:
        print(e)
        raise RuntimeError("ERROR EN GET")
    finally:
        conn.close()

user_name = os.environ.get('default')
password = os.environ.get('pnQI1h7sNfFK')
host = os.environ.get('ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech')
db_name = os.environ.get('verceldb')

# Función para obtener eventos desde la base de datos

def get_db_connection():
    try:
        # Crear la conexión a la base de datos
        conn = psycopg2.connect(
            host=host,
            user=user_name,
            password=password,
            database=db_name,
            connect_timeout=5
        )
    except psycopg2.Error as e:
        print(e)
        raise RuntimeError("ERROR EN CONEXION")