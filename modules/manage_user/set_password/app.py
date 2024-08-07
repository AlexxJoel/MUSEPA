import json
import boto3
from botocore.exceptions import ClientError


def lambda_handler(event, __):
    secrets = get_secrets()
    REGION_NAME = secrets['REGION_NAME']
    USER_POOL_ID = secrets['USER_POOL_ID']
    CLIENT_ID = secrets['CLIENT_ID']
    client = boto3.client('cognito-idp', region_name=REGION_NAME)
    try:
        # parsea el body del evento
        body_parameters = json.loads(event['body'])
        username = body_parameters.get('username')
        temporary_password = body_parameters.get('temporary_password')
        new_password = body_parameters.get('new_password')

        # Autentica al usuario con la contraseña temporal
        response = client.admin_initiate_auth(
            UserPoolId=USER_POOL_ID,
            ClientId=CLIENT_ID,
            AuthFlow='ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME': username,
                'PASSWORD': temporary_password
            }
        )

        if response['ChallengeName'] == 'NEW_PASSWORD_REQUIRED':
            client.respond_to_auth_challenge(
                ClientId=CLIENT_ID,
                ChallengeName='NEW_PASSWORD_REQUIRED',
                Session=response['Session'],
                ChallengeResponses={
                    'USERNAME': username,
                    'NEW_PASSWORD': new_password,
                    'email_verified': 'true'
                }
            )

        return {
            'statusCode': 200,
            'body': json.dumps({"message": "Password changed successfully."})
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
