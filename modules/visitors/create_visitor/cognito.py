import json
import boto3
from botocore.exceptions import ClientError


# Get secrets from AWS Secrets Manager to connect to cognito

def save_visitor_cognito(email, password):


    # Get secrets from AWS, it's only one secret in this case (Object)
    secrets = get_secrets()
    REGION_NAME = "us-west-1"
    # Get the values from the secret
    USER_POOL_ID = secrets['USER_POOL_ID']
    # CLIENT_ID = secrets['CLIENT_ID']

    try:
        # Create a boto3 client to connect to cognito
        client = boto3.client('cognito-idp', region_name=REGION_NAME)

        # Create a user in cognito
        response = client.admin_create_user(
            UserPoolId=USER_POOL_ID,
            Username=email,
            UserAttributes=[
                {
                    'Name': 'email',
                    'Value': email
                },
                {
                    'Name': 'email_verified',
                    'Value': 'true'
                }
            ],
            TemporaryPassword=password,
            MessageAction='SUPPRESS'
        )

        print(f"Answer from cognito: {response} create user")

        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            return {'statusCode': 400, 'body': json.dumps({"error": "Error creating user"})}

        # Add the user to the group 'visitor'
        response = client.admin_add_user_to_group(
            UserPoolId=USER_POOL_ID,
            Username=email,
            GroupName='visitor'
        )

        print(f"Answer from cognito: {response} add group")

        if response['ResponseMetadata']['HTTPStatusCode'] != 200:
            return {'statusCode': 400, 'body': json.dumps({"error": "Error adding user to group"})}

        return {'statusCode': 200, 'body': json.dumps({"message": "User created successfully, verification email sent."})}

    except ClientError as e:
        # If cognito fails, rollback the database
        return {'statusCode': 400, 'body': json.dumps({"error": e.response['Error']['Message']})}

    except Exception as e:
        # Handle rollback
        return {'statusCode': 500, 'body': json.dumps({"error": e.response['Error']['Message']})}


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
