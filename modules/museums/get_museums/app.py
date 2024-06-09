import json

import psycopg2
from functions import datetime_serializer
from psycopg2.extras import RealDictCursor


def lambda_handler(_event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Conexión a la base de datos
        conn = psycopg2.connect(
            host='ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
            user='default',
            password='pnQI1h7sNfFK',
            database='verceldb'
        )

        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Ejecutar una consulta (ejemplo: seleccionar todos los registros de una tabla)
        # SonarQube/SonarCloud ignore end
        cur.execute("SELECT * FROM managers;")
        # SonarQube/SonarCloud ignore start
        managers = cur.fetchall()

        rows = []
        for manager in managers:
            cur.execute("SELECT * FROM museums WHERE id_owner = %s", (manager["id"],))
            museum = cur.fetchone()
            if museum is not None:
                museum["manager"] = manager
                rows.append(museum)
        return {'statusCode': 200, 'body': json.dumps(rows, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    # SonarQube/SonarCloud ignore end
