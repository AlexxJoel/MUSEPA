import unittest
from unittest.mock import patch, MagicMock
import json
from modules.manage_user.set_password.app import lambda_handler,get_secrets
from botocore.exceptions import ClientError


class TestLambdaHandler(unittest.TestCase):

    @patch('modules.manage_user.set_password.app.get_secrets')
    @patch('modules.manage_user.set_password.app.boto3.client')
    def test_lambda_handler_password_change_success(self, mock_boto_client, mock_get_secrets):
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'client-id',
            'USER_POOL_ID': 'user-pool-id'
        }

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Simula la respuesta de admin_initiate_auth
        mock_client.admin_initiate_auth.return_value = {
            'ChallengeName': 'NEW_PASSWORD_REQUIRED',
            'Session': 'test-session'
        }

        # Evento simulado
        event = {
            "body": json.dumps({
                "username": "testuser",
                "temporary_password": "tempPass123",
                "new_password": "newPass456"
            })
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Password changed successfully', json.loads(response['body'])['message'])

    @patch('modules.manage_user.set_password.app.get_secrets')
    @patch('modules.manage_user.set_password.app.boto3.client')
    def test_lambda_handler_client_error(self, mock_boto_client, mock_get_secrets):
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'client-id',
            'USER_POOL_ID': 'user-pool-id'
        }

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client

        # Simula un ClientError
        mock_client.admin_initiate_auth.side_effect = ClientError(
            {"Error": {"Message": "User does not exist"}},
            "AdminInitiateAuth"
        )

        event = {
            "body": json.dumps({
                "username": "testuser",
                "temporary_password": "tempPass123",
                "new_password": "newPass456"
            })
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('User does not exist', json.loads(response['body'])['error'])



class TestGetSecrets(unittest.TestCase):

    @patch('modules.manage_user.set_password.app.boto3.session.Session')
    def test_get_secrets_success(self, mock_boto_session):
        # Configuración del mock para simular una respuesta exitosa de Secrets Manager
        mock_client = MagicMock()
        mock_boto_session.return_value.client.return_value = mock_client

        mock_client.get_secret_value.return_value = {
            'SecretString': json.dumps({
                'REGION_NAME': 'us-west-1',
                'CLIENT_ID': 'client-id',
                'USER_POOL_ID': 'user-pool-id'
            })
        }

        secrets = get_secrets()

        expected_secrets = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'client-id',
            'USER_POOL_ID': 'user-pool-id'
        }

        self.assertEqual(secrets, expected_secrets)

    @patch('modules.manage_user.set_password.app.boto3.session.Session')
    def test_get_secrets_exception(self, mock_boto_session):
        # Configuración del mock para simular una excepción
        mock_client = MagicMock()
        mock_boto_session.return_value.client.return_value = mock_client

        mock_client.get_secret_value.side_effect = Exception("Secrets Manager error")

        with self.assertRaises(Exception) as context:
            get_secrets()

        self.assertEqual(str(context.exception), "Secrets Manager error")



if __name__ == '__main__':
    unittest.main()
