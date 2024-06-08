import json
import psycopg2
from functions import (datetime_serializer, serialize_rows)

def lambda_handler(event, context):
    try:
        # Conexión a la base de datos
        conn = psycopg2.connect(
            host='ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
            user = 'default',
            password = 'pnQI1h7sNfFK',
            database = 'verceldb'
        )

        cur = conn.cursor()

        # Ejecutar una consulta (ejemplo: seleccionar todos los registros de una tabla)
        cur.execute("SELECT * FROM works;")

        rows = cur.fetchall()

        cur.close()
        conn.close()

        return  {
            'statusCode': 200,
            'body': json.dumps(serialize_rows(rows, cur), default=datetime_serializer)
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps(str(e))
        }
