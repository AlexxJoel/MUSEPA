import json

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, __):
    # Se colocan las credenciales que obtuvimos al generar lo de cognito
    # Configura el cliente de cognito
    client = boto3.client('cognito-idp', region_name='us-west-1')
    client_id = "2o20sdj0jd56hcfs13tjj28edg"

    try:
        body_parameters = json.loads(event["body"])
        username = body_parameters.get('username')
        password = body_parameters.get('password')

        response = client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': password
            }
        )

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
