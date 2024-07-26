import json
import jwt
import psycopg2
from functions import datetime_serializer
from psycopg2.extras import RealDictCursor
from modules.museums.get_museums.connect_db import get_db_connection


def lambda_handler(_event, _context):

    conn = None
    cur = None
    try:

        # Obtener el token de los encabezados
        token = _event['headers']['Authorization'].split(' ')[1]
        # Decodificar el token
        # Nota: En un entorno de producción, debes verificar la firma del token
        decoded_token = jwt.decode(token, options={"verify_signature": False})
        # Obtener el rol del token
        role = decoded_token.get('role')
        # Revocar permiso si el rol es "visitor"
        if role == "visitor":
            return {'statusCode': 403, 'body': json.dumps({"error": "Access denied: insufficient permissions"})}

        # SonarQube/SonarCloud ignore start
        # Database connection
        conn = get_db_connection()

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # SonarQube/SonarCloud ignore end
        # Find all managers
        cur.execute("SELECT * FROM museums")
        # SonarQube/SonarCloud ignore start

        museums = cur.fetchall()

        return {'statusCode': 200, 'body': json.dumps({"data": museums}, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    # SonarQube/SonarCloud ignore end
