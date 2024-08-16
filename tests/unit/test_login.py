import unittest
from unittest.mock import patch, MagicMock
import json
from botocore.exceptions import ClientError
from modules.manage_user.login.app import lambda_handler, get_secrets

class TestLoginLambdaHandler(unittest.TestCase):

    @patch('boto3.session.Session.client')
    def test_get_secrets_success(self, mock_boto_client):
        # Mock del cliente de Secrets Manager
        mock_secrets_manager = MagicMock()
        mock_boto_client.return_value = mock_secrets_manager

        # Configuración del valor de retorno del mock
        mock_secrets_manager.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'REGION_NAME': 'us-west-1',
                'CLIENT_ID': 'example_client_id'
            })
        }

        # Ejecutar la función
        secrets = get_secrets()

        # Verificaciones
        self.assertIn('REGION_NAME', secrets)
        self.assertIn('CLIENT_ID', secrets)
        mock_secrets_manager.get_secret_value.assert_called_once_with(SecretId='prod/musepa')

    @patch('boto3.client')
    @patch('modules.manage_user.login.app.get_secrets')
    def test_lambda_handler_success(self, mock_get_secrets, mock_boto_client):
        # Mock de la función get_secrets
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'example_client_id'
        }

        # Mock del cliente de Cognito
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client

        # Simulación de la respuesta exitosa de Cognito
        mock_cognito_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'IdToken': 'example_id_token',
                'AccessToken': 'example_access_token',
                'RefreshToken': 'example_refresh_token'
            }
        }

        # Simulación de la respuesta de listado de grupos
        mock_cognito_client.admin_list_groups_for_user.return_value = {
            'Groups': [
                {'GroupName': 'manager'}
            ]
        }

        # Datos de prueba
        event = {
            "body": json.dumps({
                "username": "testuser",
                "password": "TestPassword123!"
            })
        }

        # Ejecutar la función
        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertIn('id_token', body)
        self.assertIn('access_token', body)
        self.assertIn('refresh_token', body)
        self.assertEqual(body['role'], 'manager')

    @patch('boto3.client')
    @patch('modules.manage_user.login.app.get_secrets')
    def test_lambda_handler_new_password_required(self, mock_get_secrets, mock_boto_client):
        # Mock de la función get_secrets
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'example_client_id'
        }

        # Mock del cliente de Cognito con el desafío de nueva contraseña
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client
        mock_cognito_client.initiate_auth.return_value = {
            'ChallengeName': 'NEW_PASSWORD_REQUIRED'
        }

        # Datos de prueba
        event = {
            "body": json.dumps({
                "username": "testuser",
                "password": "TestPassword123!"
            })
        }

        # Ejecutar la función
        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Access denied', response['body'])

    @patch('boto3.client')
    @patch('modules.manage_user.login.app.get_secrets')
    def test_lambda_handler_client_error(self, mock_get_secrets, mock_boto_client):
        # Mock de la función get_secrets
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'example_client_id'
        }

        # Mock del cliente de Cognito con un error
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client
        mock_cognito_client.initiate_auth.side_effect = ClientError(
            error_response={'Error': {'Message': 'Invalid credentials'}},
            operation_name='InitiateAuth'
        )

        # Datos de prueba
        event = {
            "body": json.dumps({
                "username": "testuser",
                "password": "TestPassword123!"
            })
        }

        # Ejecutar la función
        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Invalid credentials', response['body'])

    @patch('boto3.client')
    @patch('modules.manage_user.login.app.get_secrets')
    def test_lambda_handler_general_exception(self, mock_get_secrets, mock_boto_client):
        # Mock de la función get_secrets
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'example_client_id'
        }

        # Mock del cliente de Cognito con un error general
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client
        mock_cognito_client.initiate_auth.side_effect = Exception('Something went wrong')

        # Datos de prueba
        event = {
            "body": json.dumps({
                "username": "testuser",
                "password": "TestPassword123!"
            })
        }

        # Ejecutar la función
        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Something went wrong', response['body'])

if __name__ == '__main__':
    unittest.main()
