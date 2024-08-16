import unittest
from unittest.mock import patch, MagicMock
import json
from botocore.exceptions import ClientError
from modules.manage_user.insert_user_pool.app import lambda_handler, get_secrets

class TestLambdaHandler(unittest.TestCase):

    @patch('boto3.session.Session.client')
    def test_get_secrets_success(self, mock_boto_client):
        # Mockear el cliente de Secrets Manager
        mock_secrets_manager = MagicMock()
        mock_boto_client.return_value = mock_secrets_manager

        # Configurar el valor de retorno del mock
        mock_secrets_manager.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'REGION_NAME': 'us-west-1',
                'USER_POOL_ID': 'us-west-1_testPool'
            })
        }

        # Ejecutar la función
        secrets = get_secrets()

        # Verificaciones
        self.assertIn('REGION_NAME', secrets)
        self.assertIn('USER_POOL_ID', secrets)
        mock_secrets_manager.get_secret_value.assert_called_once_with(SecretId='prod/musepa')

    @patch('boto3.client')
    @patch('modules.manage_user.insert_user_pool.app.get_secrets')
    def test_lambda_handler_success(self, mock_get_secrets, mock_boto_client):
        # Mockear la función get_secrets
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'USER_POOL_ID': 'us-west-1_testPool'
        }

        # Mockear el cliente de Cognito
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client

        # Datos de prueba
        event = {
            "body": json.dumps({
                "email": "test@example.com",
                "phone_number": "+123456789",
                "user_name": "testuser",
                "password": "TestPassword123!"
            })
        }

        # Ejecutar la función
        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('User created successfully', response['body'])
        mock_cognito_client.admin_create_user.assert_called_once_with(
            UserPoolId='us-west-1_testPool',
            Username='testuser',
            UserAttributes=[
                {'Name': 'email', 'Value': 'test@example.com'},
                {"Name": 'email_verified', 'Value': 'false'}
            ],
            TemporaryPassword='TestPassword123!'
        )
        mock_cognito_client.admin_add_user_to_group.assert_called_once_with(
            UserPoolId='us-west-1_testPool',
            Username='testuser',
            GroupName='manager'
        )

    @patch('boto3.client')
    @patch('modules.manage_user.insert_user_pool.app.get_secrets')
    def test_lambda_handler_missing_parameters(self, mock_get_secrets, mock_boto_client):
        # Datos de prueba incompletos
        event = {
            "body": json.dumps({
                "email": "test@example.com",
                "user_name": "testuser"
            })
        }

        # Ejecutar la función
        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('missing input parameters', response['body'])

    @patch('boto3.client')
    @patch('modules.manage_user.insert_user_pool.app.get_secrets')
    def test_lambda_handler_client_error(self, mock_get_secrets, mock_boto_client):
        # Mockear la función get_secrets
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'USER_POOL_ID': 'us-west-1_testPool'
        }

        # Mockear el cliente de Cognito con un error
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client
        mock_cognito_client.admin_create_user.side_effect = ClientError(
            error_response={'Error': {'Message': 'An error occurred'}},
            operation_name='AdminCreateUser'
        )

        # Datos de prueba
        event = {
            "body": json.dumps({
                "email": "test@example.com",
                "phone_number": "+123456789",
                "user_name": "testuser",
                "password": "TestPassword123!"
            })
        }

        # Ejecutar la función
        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('An error occurred', response['body'])

if __name__ == '__main__':
    unittest.main()
