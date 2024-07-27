import json
from urllib.request import urlopen

import jwt
from jwt import PyJWKClient


def lambda_handler(event, _context):
    token = event['headers']['Authorization'].split()[1]

    # Reemplaza con tu User Pool ID y App Client ID
    user_pool_id = 'us-west-1_3onWfQPhK'
    app_client_id = '2o20sdj0jd56hcfs13tjj28edg'

    # Rol requerido para acceso
    required_role = 'visitor'

    # Descarga el JWK del User Pool
    url = f'https://cognito-idp.us-west-1.amazonaws.com/{user_pool_id}/.well-known/jwks.json'

    with urlopen(url) as f:
        jwks = json.loads(f.read())

    # Obtiene la clave pública
    jwk = PyJWKClient(jwks)
    signing_key = jwk.get_signing_key_from_jwt(token)

    # Decodifica el token JWT
    decoded_token = jwt.decode(token, signing_key.key, algorithms=['RS256'], options={"verify_signature": True})

    # Verifica los roles en los claims del token
    user_roles = decoded_token.get('cognito:groups', [])

    # Verifica si el usuario tiene el rol requerido
    if required_role not in user_roles:
        return {'statusCode': 403, 'body': json.dumps('Forbidden')}

    return {'statusCode': 200, 'body': json.dumps('Authorized')}