import json

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, __):
    secrets = get_secrets()
    REGION_NAME = secrets['REGION_NAME']
    CLIENT_ID = secrets['CLIENT_ID']
    # Se colocan las credenciales que obtuvimos al generar lo de cognito
    # Configura el cliente de cognito
    client = boto3.client('cognito-idp', region_name=REGION_NAME)

    try:
        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')
        password = body_parameters.get('password')

        response = client.initiate_auth(
            ClientId=CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )

        if 'ChallengeName' in response and response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            return {
                'statusCode': 401,
                'body': json.dumps({"error": "Access denied. Please, change the temporary password."})
            }

        id_token = response['AuthenticationResult']['IdToken']
        access_token = response['AuthenticationResult']['AccessToken']
        refresh_token = response['AuthenticationResult']['RefreshToken']

        # Obten el grupo de usuarios
        user_groups = client.admin_list_groups_for_user(
            Username=username,
            UserPoolId='us-west-1_3onWfQPhK'  # Reemplaza las credenciales
        )

        # Determina el rol basado en el grupo
        role = None
        if user_groups['Groups']:
            role = user_groups['Groups'][0]['GroupName']  # Asumiendo un usuario pertenece a un solo grupo

        return {
            'statusCode': 200,
            'body': json.dumps({
                'id_token': id_token,
                'access_token': access_token,
                'refresh_token': refresh_token,
                'role': role
            })
        }
    except ClientError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({"error": e.response['Error']['Message']})
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({"error": str(e)})
        }


def get_secrets():
    secret_name = "prod/musepa/vercel/postgres"
    region_name = "us-west-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager', region_name=region_name)

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)

    except Exception as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)
