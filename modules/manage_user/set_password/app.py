import json
import boto3
from botocore.exceptions import ClientError

def lambda_handler(event,__):
    client = boto3.client('cognito-idp', region_name='us-esast-1')
    user_pool_id = "us-east-1_bXBpM3EPU"
    client_id = ""
    try:
        #parsea el body del evento
        body_parameters = json.loads(event['body'])
        username = body_parameters.get('username')
        temporary_password = body_parameters.get('temporary_password')
        new_password = body_parameters.get('new_password')

        #Autentica al usuario con la contraseña temporal
        response = client.admin_initiate_auth(
            UserPoolId = user_pool_id,
            ClientId= client_id,
            AuthFlow = 'ADMIN_USER_PASSWORD_AUTH',
            AuthParameters={
                'USERNAME':username,
                'PASSWORD': temporary_password
            }
        )

        if response['challengeName'] == 'NEW_PASSWORD_REQUIRED':
            client.respond_to_auth_challenge(
                ClientId=client_id,
                ChallengeNAme='NEW_PASSWORD_REQUIRED',
                Session=response['Session'],
                ChallengeResponses={
                    'USERNAME': username,
                    'NEW_PASSWORD':new_password,
                    'email_verified':'true'
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