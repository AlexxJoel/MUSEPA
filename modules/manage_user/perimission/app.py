import json
import boto3
import jwt
from jwt import PyJWKClient
from urllib.request import urlopen


def lambda_handler(event, context):
    token = event['headers']['Authorization'].split()[1]

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

    # Token válido y rol presente
    return {
        'statusCode': 200,
        'body': json.dumps('Token y rol válidos'),
        'user': payload
    }
