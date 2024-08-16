import unittest
from unittest.mock import patch, MagicMock
import json
from botocore.exceptions import ClientError
from modules.manage_user.set_password.app import lambda_handler, get_secrets

class TestSetPasswordLambdaHandler(unittest.TestCase):

    @patch('boto3.session.Session.client')
    def test_get_secrets_success(self, mock_boto_client):
        # Mock del cliente de Secrets Manager
        mock_secrets_manager = MagicMock()
        mock_boto_client.return_value = mock_secrets_manager

        # Configuración del valor de retorno del mock
        mock_secrets_manager.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'REGION_NAME': 'us-west-1',
                'USER_POOL_ID': 'example_user_pool_id',
                'CLIENT_ID': 'example_client_id'
            })
        }

        # Ejecutar la función
        secrets = get_secrets()

        # Verificaciones
        self.assertIn('REGION_NAME', secrets)
        self.assertIn('USER_POOL_ID', secrets)
        self.assertIn('CLIENT_ID', secrets)
        mock_secrets_manager.get_secret_value.assert_called_once_with(SecretId='prod/musepa')

    @patch('boto3.client')
    @patch('modules.manage_user.set_password.app.get_secrets')
    def test_lambda_handler_success(self, mock_get_secrets, mock_boto_client):
        # Mock de la función get_secrets
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'USER_POOL_ID': 'example_user_pool_id',
            'CLIENT_ID': 'example_client_id'
        }

        # Mock del cliente de Cognito
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client

        # Simulación de la respuesta exitosa de Cognito
        mock_cognito_client.admin_initiate_auth.return_value = {
            'ChallengeName': 'NEW_PASSWORD_REQUIRED',
            'Session': 'example_session_token'
        }

        # Datos de prueba
        event = {
            "body": json.dumps({
                "username": "testuser",
                "temporary_password": "TempPass123!",
                "new_password": "NewPass123!"
            })
        }

        # Ejecutar la función
        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 200)
        body = json.loads(response['body'])
        self.assertEqual(body['message'], "Password changed successfully.")

        # Verifica que se llame al desafío de nueva contraseña
        mock_cognito_client.respond_to_auth_challenge.assert_called_once_with(
            ClientId='example_client_id',
            ChallengeName='NEW_PASSWORD_REQUIRED',
            Session='example_session_token',
            ChallengeResponses={
                'USERNAME': 'testuser',
                'NEW_PASSWORD': 'NewPass123!',
                'email_verified': 'true'
            }
        )

    @patch('boto3.client')
    @patch('modules.manage_user.set_password.app.get_secrets')
    def test_lambda_handler_client_error(self, mock_get_secrets, mock_boto_client):
        # Mock de la función get_secrets
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'USER_POOL_ID': 'example_user_pool_id',
            'CLIENT_ID': 'example_client_id'
        }

        # Mock del cliente de Cognito con un error
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client
        mock_cognito_client.admin_initiate_auth.side_effect = ClientError(
            error_response={'Error': {'Message': 'Invalid temporary password'}},
            operation_name='AdminInitiateAuth'
        )

        # Datos de prueba
        event = {
            "body": json.dumps({
                "username": "testuser",
                "temporary_password": "TempPass123!",
                "new_password": "NewPass123!"
            })
        }

        # Ejecutar la función
        response = lambda_handler(event, None)

        # Verificaciones
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Invalid temporary password', response['body'])


if __name__ == '__main__':
    unittest.main()
