import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
import boto3
from botocore.exceptions import ClientError
import jwt

from modules.managers.delete_manager.app import lambda_handler
from modules.managers.delete_manager.app import validate_connection, validate_event_path_params
from modules.managers.delete_manager.app import get_db_connection,get_secrets
from modules.managers.delete_manager.app import authorizate_user

def simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection):
    mock_validate_connection.return_value = None
    mock_validate_event_path_params.return_value = None


headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'DELETE'
}

class FakeConnection:
    """Clase que simula una conexión de psycopg2"""
    def close(self):
        pass

class FakeSecretsManagerClient:
    """Simula el cliente de Secrets Manager de boto3."""
    def get_secret_value(self, SecretId):
        if SecretId == "prod/musepa":
            return {
                'SecretString': json.dumps({
                    'POSTGRES_HOST': 'localhost',
                    'POSTGRES_PASSWORD': 'fake_password',
                    'POSTGRES_DATABASE': 'fake_database'
                })
            }
        else:
            raise ClientError(
                {"Error": {"Code": "ResourceNotFoundException"}},
                "get_secret_value"
            )

class FakeSession:
    """Simula una sesión de boto3."""
    def client(self, service_name, region_name):
        if service_name == 'secretsmanager' and region_name == 'us-west-1':
            return FakeSecretsManagerClient()
        else:
            raise ValueError("Unsupported service or region")

class TestFindManager(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.managers.delete_manager.app.get_secrets")
    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    @patch("modules.managers.delete_manager.app.validate_connection")
    @patch("modules.managers.delete_manager.app.validate_event_path_params")
    @patch("boto3.client")
    def test_delete_manager_success(self, mock_boto_client, mock_validate_event_path_params, mock_validate_connection,
                                    mock_authorizate_user, mock_get_db_connection, mock_get_secrets):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Simula la obtención de secretos
        mock_get_secrets.return_value = {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PASSWORD': 'password',
            'POSTGRES_DATABASE': 'test_db',
            'USER_POOL_ID': 'us-west-1_XXXXXXXXX'
        }

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        # Simula los datos devueltos por el cursor de la base de datos
        self.mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "name": "Alejandro",
                "surname": "Morellano",
                "lastname": "Alvarez",
                "phone_number": "+1234567870",
                "address": "123 Main St, Anytoiwn, USA",
                "birthdate": "1990-02-01",
                "id_user": 18,
                'id_museum': 1
            },
            {
                "username": "alejandro.morellano"
            }
        ]

        # Simula la eliminación en Cognito
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client
        mock_cognito_client.admin_delete_user.return_value = {}

        # Simula el evento Lambda
        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}
        }
        result = lambda_handler(event, None)

        # Verifica que el resultado sea el esperado
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Manager deleted successfully"}))

        # Verifica que las conexiones y cursores se cierren correctamente
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    @patch("modules.managers.delete_manager.app.validate_connection")
    @patch("modules.managers.delete_manager.app.validate_event_path_params")
    def test_find_manager_not_found(self, mock_validate_event_path_params, mock_validate_connection,
                                    mock_authorizate_user, mock_get_db_connection):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.return_value = None

        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '999'}}
        result = lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(result["body"], json.dumps({"error": "Manager not found"}))

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    def test_lambda_invalid_conn(self,  mock_authorizate_user, mock_get_db_connection):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = None

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        event = { 'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    def test_lambda_invalid_path_parameters(self,  mock_authorizate_user, mock_get_db_connection):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        event = {'pathParameters': None}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 400)

    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    @patch("modules.managers.delete_manager.app.validate_connection")
    @patch("modules.managers.delete_manager.app.validate_event_path_params")
    def test_lambda_handler_500_error(self, mock_validate_event_path_params, mock_validate_connection,
                                      mock_authorizate_user, mock_get_db_connection):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.execute.side_effect = Exception("Simulated database error")

        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Simulated database error"}))


class TestValidations(TestCase):
    def test_validate_connection_success(self):
        conn = MagicMock()
        result = validate_connection(conn)
        self.assertIsNone(result)

    def test_validate_connection_failure(self):
        conn = None
        result = validate_connection(conn)
        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    def test_validate_event_path_params_success(self):
        event = {'pathParameters': {'id': '7'}}
        result = validate_event_path_params(event)
        self.assertIsNone(result)

    def test_validate_event_path_params_missing_path_parameters(self):
        event = {}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Path parameters is missing from the request."}))

    def test_validate_event_path_params_null_path_parameters(self):
        event = {'pathParameters': None}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Path parameters is null."}))

    def test_validate_event_path_params_missing_id(self):
        event = {'pathParameters': {}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID is missing from the path parameters."}))

    def test_validate_event_path_params_null_id(self):
        event = {'pathParameters': {'id': None}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID is missing from the path parameters."}))

    def test_validate_event_path_params_invalid_id_type(self):
        event = {'pathParameters': {'id': 'abc'}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID data type is wrong."}))

    def test_validate_event_path_params_invalid_id_value(self):
        event = {'pathParameters': {'id': '0'}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID invalid value."}))


class TestConnectDB(TestCase):
    @patch('modules.managers.delete_manager.app.psycopg2.connect')
    @patch('modules.managers.delete_manager.app.get_secrets')
    def test_get_db_connection(self, mock_get_secrets, mock_psycopg2_connect):
        # Simula la respuesta de get_secrets
        mock_get_secrets.return_value = {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PASSWORD': 'fake_password',
            'POSTGRES_DATABASE': 'fake_database'
        }

        # Crea una instancia de la conexión simulada
        fake_connection = FakeConnection()
        mock_psycopg2_connect.return_value = fake_connection

        # Llama a la función que se está probando
        conn = get_db_connection()

        # Verifica que get_secrets fue llamada una vez
        mock_get_secrets.assert_called_once()

        # Verifica que psycopg2.connect fue llamada con los parámetros correctos
        mock_psycopg2_connect.assert_called_once_with(
            host='localhost',
            user='default',
            password='fake_password',
            database='fake_database'
        )

        # Verifica que la conexión devuelta es la misma que la simulada
        self.assertEqual(conn, fake_connection)

    def test_get_secrets_success(self):
        # Parcha la sesión de boto3 con una sesión simulada
        original_session = boto3.session.Session
        try:
            boto3.session.Session = FakeSession
            secrets = get_secrets()
            expected_secrets = {
                'POSTGRES_HOST': 'localhost',
                'POSTGRES_PASSWORD': 'fake_password',
                'POSTGRES_DATABASE': 'fake_database'
            }
            self.assertEqual(secrets, expected_secrets)
        finally:
            # Restaura la sesión original
            boto3.session.Session = original_session

    def test_get_secrets_failure(self):
        # Parcha la sesión de boto3 con una sesión simulada que falla
        original_session = boto3.session.Session
        try:
            class FailingSecretsManagerClient:
                def get_secret_value(self, SecretId):
                    raise ClientError({"Error": {"Code": "ResourceNotFoundException"}},"get_secret_value")

            class FailingSession:
                def client(self, service_name, region_name):
                    return FailingSecretsManagerClient()

            boto3.session.Session = FailingSession

            with self.assertRaises(ClientError):
                get_secrets()
        finally:
            # Restaura la sesión original
            boto3.session.Session = original_session

class TestAuthorization(TestCase):
    def test_authorization_success(self):
        # Simula un evento con un token válido y un rol permitido
        token_payload = {
            "cognito:groups": ["admin"]
        }
        token = jwt.encode(token_payload, key="secret", algorithm="HS256")
        event = {
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        }

        result = authorizate_user(event)
        self.assertIsNone(result)

    def test_authorization_visitor_role(self):
        # Simula un evento con un token válido pero con el rol 'visitor'
        token_payload = {
            "cognito:groups": ["visitor"]
        }
        token = jwt.encode(token_payload, key="secret", algorithm="HS256")
        event = {
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        }

        result = authorizate_user(event)
        expected_result = {
            'statusCode': 403,
            'body': json.dumps({"error": "Access denied: insufficient permissions"}),
            'headers': headers
        }
        self.assertEqual(result, expected_result)

    def test_authorization_no_token(self):
        # Simula un evento sin token en los headers
        event = {
            "headers": {
                "Authorization": ""
            }
        }

        with self.assertRaises(IndexError):
            authorizate_user(event)

if __name__ == '__main__':
    unittest.main()
