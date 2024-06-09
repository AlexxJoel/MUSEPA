import json

import psycopg2
from functions import datetime_serializer
from psycopg2.extras import RealDictCursor


def lambda_handler(_event, _context):
    conn = None
    cur = None
    try:
        # Conexión a la base de datos
        conn = psycopg2.connect(
            host="ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech",
            user="default",
            password="pnQI1h7sNfFK",
            database="verceldb",
        )

        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM users")
        users = cur.fetchall()

        rows = []
        for user in users:
            cur.execute("SELECT * FROM managers WHERE id_user = %s", (user["id"],))
            manager = cur.fetchone()
            if manager is not None:
                manager["user"] = user
                rows.append(manager)
        return {"statusCode": 200, "body": json.dumps(rows, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
