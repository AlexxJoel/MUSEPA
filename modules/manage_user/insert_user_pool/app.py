import json

import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, context):
    secrets = get_secrets()
    REGION_NAME = secrets['REGION_NAME']
    USER_POOL_ID = secrets['USER_POOL_ID']
    body_parameters = json.loads(event["body"])
    email = body_parameters.get('email')
    phone_number = body_parameters.get('phone_number')
    user_name = body_parameters.get('user_name')
    password = body_parameters.get('password')
    role = "manager"

    print("Extracted parameters:", email, phone_number, user_name, password)

    if email is None or phone_number is None or user_name is None or password is None:
        return {
            "statusCode": 400,
            "body": json.dumps({"message": "missing input parameters"})
        }

    try:
        # Se colocan las credenciales que obtuvimos al generar lo de cognito
        # Configura el cliente de cognito
        client = boto3.client('cognito-idp', region_name=REGION_NAME)

        # Crea el usuario con correo no verificado y contraseña temporal que se envia automaticamente a su correo
        client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=user_name,
            UserAttributes=[
                {'Name': 'email', 'Value': email},
                {"Name": 'email_verified', 'Value': 'false'}
            ],
            TemporaryPassword=password
        )

        client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=user_name,
            GroupName=role
        )

        # Se manda a llamar lo que se pide de registro del usuario ya sea manager o visitor

        return {
            'statusCode': 200,
            'body': json.dumps({"message": "User created successfully, verification email sent."})
        }
    except ClientError as e:
        return {
            'statusCode': 400,
            'body': json.dumps({"error": e.response['Error']['Message']})
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
