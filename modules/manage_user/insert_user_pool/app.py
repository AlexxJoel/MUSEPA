import json

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event,__):
    body_parameters = json.loads(event["body"])
    email = body_parameters.get('email')
    phone_number = body_parameters.get('phone_nomber')
    user_name = body_parameters('user_name')
    password = body_parameters.get('password')
    role="visitor"

    if email is None or phone_number is None or user_name is None or password is None:
        return {
            "statusCode":400,
            "body":json.dumps({"message":"missing input parameters"})
        }
    try:
        # Se colocan las credenciales que obtuvimos al generar lo de cognito
        # Configura el cliente de cognito
        client = boto3.client('cognito-idp',region_name='us-esast-1')
        user_pool_id = "us-east-1_bXBpM3EPU"

        # Crea el usuario con correo no verificado y contraseña temporal que se envia automaticamente a su correo
        client.admin_create_user(
            UserPoolId=user_pool_id,
            Username=user_name,
            UserAttributes =[
                {'Name':'email','Value':email},
                {"Name":'email_verified','Value':'false'}
            ],
            TemporaryPassword=password
        )

        client.admin_create_user_to_group(
            UserPoolId=user_pool_id,
            Username=user_name,
            GroupName=role
        )

        #Se manda a llamar lo que se pide de registro del usuario ya sea manager o visitor

        return{
            'statusCode':200,
            'body': json.dumps({"message":"User created successfully, verification email sent."})
        }
    except ClientError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({"error":e.response['Error']['Message']})
        }

