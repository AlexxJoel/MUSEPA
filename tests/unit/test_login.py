import unittest
from unittest.mock import patch, MagicMock
import json
from botocore.exceptions import ClientError
from modules.manage_user.login.app import lambda_handler, get_secrets

class TestLambdaHandler(unittest.TestCase):
    @patch('modules.manage_user.login.app.get_secrets')
    @patch('modules.manage_user.login.app.boto3.client')
    def test_lambda_handler_success(self, mock_boto_client, mock_get_secrets):
        # Simula los secretos que se obtienen
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'client-id',
            'USER_POOL_ID': 'user-pool-id'
        }

        # Simula la respuesta de Cognito
        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.initiate_auth.return_value = {
            'AuthenticationResult': {
                'IdToken': 'test-id-token',
                'AccessToken': 'test-access-token',
                'RefreshToken': 'test-refresh-token'
            }
        }
        mock_client.admin_list_groups_for_user.return_value = {
            'Groups': [{'GroupName': 'test-group'}]
        }

        event = {
            "body": json.dumps({
                "username": "testuser",
                "password": "testpassword"
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 200)
        self.assertIn('id_token', json.loads(response['body']))

    @patch('modules.manage_user.login.app.get_secrets')
    @patch('modules.manage_user.login.app.boto3.client')
    def test_lambda_handler_new_password_required(self, mock_boto_client, mock_get_secrets):
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'client-id',
            'USER_POOL_ID': 'user-pool-id'
        }

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.initiate_auth.return_value = {
            'ChallengeName': 'NEW_PASSWORD_REQUIRED'
        }

        event = {
            "body": json.dumps({
                "username": "testuser",
                "password": "testpassword"
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 401)
        self.assertIn('Access denied', json.loads(response['body'])['error'])

    @patch('modules.manage_user.login.app.get_secrets')
    @patch('modules.manage_user.login.app.boto3.client')
    def test_lambda_handler_client_error(self, mock_boto_client, mock_get_secrets):
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'client-id',
            'USER_POOL_ID': 'user-pool-id'
        }

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.initiate_auth.side_effect = ClientError(
            {"Error": {"Message": "User does not exist"}}, "InitiateAuth"
        )

        event = {
            "body": json.dumps({
                "username": "testuser",
                "password": "wrongpassword"
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('User does not exist', json.loads(response['body'])['error'])

    @patch('modules.manage_user.login.app.get_secrets')
    @patch('modules.manage_user.login.app.boto3.client')
    def test_lambda_handler_exception(self, mock_boto_client, mock_get_secrets):
        mock_get_secrets.return_value = {
            'REGION_NAME': 'us-west-1',
            'CLIENT_ID': 'client-id',
            'USER_POOL_ID': 'user-pool-id'
        }

        mock_client = MagicMock()
        mock_boto_client.return_value = mock_client
        mock_client.initiate_auth.side_effect = Exception("Unknown error")

        event = {
            "body": json.dumps({
                "username": "testuser",
                "password": "testpassword"
            })
        }

        response = lambda_handler(event, None)
        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Unknown error', json.loads(response['body'])['error'])


class TestGetSecrets(unittest.TestCase):

    @patch('modules.manage_user.login.app.boto3.session.Session')
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

    @patch('modules.manage_user.login.app.boto3.session.Session')
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
