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

        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

        rows = []
        for user in users:
            print("User:", user)
            cur.execute("SELECT * FROM visitors WHERE id_user = %s", (user[0],))
            visitors = cur.fetchall()
            for visitor in visitors:
                rows = json.dumps({
                    "visitor": {
                        "user": user,
                        "visitor": visitor
                    },
                })

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
