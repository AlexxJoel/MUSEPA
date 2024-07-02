import json
from urllib.request import urlopen

import jwt
import psycopg2
from jwt import PyJWKClient

from functions import datetime_serializer
from psycopg2.extras import RealDictCursor


def lambda_handler(_event, _context):
    token = _event['headers']['Authorization'].split()[1]

    # Reemplaza con tu User Pool ID y App Client ID
    user_pool_id = 'us-west-1_3onWfQPhK'
    app_client_id = '2o20sdj0jd56hcfs13tjj28edg'

    # Rol requerido para acceso
    required_role = 'visitor'

    # URL de las claves públicas de Cognito
    keys_url = f'https://cognito-idp.us-west-1.amazonaws.com/{user_pool_id}/.well-known/jwks.json'

    # Obtén las claves públicas
    response = urlopen(keys_url)
    keys = json.loads(response.read())['keys']

    # Obtén el encabezado del token para determinar cuál clave usar
    headers = jwt.get_unverified_header(token)
    kid = headers['kid']

    # Encuentra la clave correspondiente
    key = next((k for k in keys if k['kid'] == kid), None)
    if key is None:
        raise ValueError('Clave pública no encontrada')

    # Decodifica y valida el token
    jwk_client = PyJWKClient(keys_url)
    signing_key = jwk_client.get_signing_key_from_jwt(token)

    try:
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=['RS256'],
            audience=app_client_id
        )
    except jwt.ExpiredSignatureError:
        return {'statusCode': 401, 'body': json.dumps('Token expirado')}
    except jwt.InvalidTokenError:
        return {'statusCode': 401, 'body': json.dumps('Token inválido')}

    # Verifica si el usuario tiene el rol requerido
    if 'cognito:groups' not in payload or required_role not in payload['cognito:groups']:
        return {'statusCode': 403, 'body': json.dumps('Acceso denegado. Rol requerido no presente')}

    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Database connection
        conn = psycopg2.connect(
            host='ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
            user='default',
            password='pnQI1h7sNfFK',
            database='verceldb'
        )

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # SonarQube/SonarCloud ignore end
        # Find all managers
        cur.execute("SELECT * FROM managers")
        # SonarQube/SonarCloud ignore start

        managers = cur.fetchall()

        # Find all museums by manager id
        rows = []
        for manager in managers:
            cur.execute("SELECT * FROM museums WHERE id_owner = %s", (manager["id"],))
            museum = cur.fetchone()
            if museum is not None:
                museum["manager"] = manager
                rows.append(museum)

        return {'statusCode': 200, 'body': json.dumps({"data": rows}, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    # SonarQube/SonarCloud ignore end
