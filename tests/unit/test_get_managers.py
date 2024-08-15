import json
import unittest
from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock
import boto3
import jwt
from botocore.exceptions import ClientError

from modules.managers.get_managers.app import lambda_handler
from modules.managers.get_managers.app import datetime_serializer
from modules.managers.get_managers.app import validate_connection
from modules.managers.get_managers.app import get_db_connection,get_secrets
from modules.managers.get_managers.app import authorizate_user

def simulate_valid_validations(mock_validate_connection):
    mock_validate_connection.return_value = None

headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET'
}

class FakeConnection:
    """Clase que simula una conexión de psycopg2"""
    def close(self):
        pass

class FakeSecretsManagerClient:
    """Simula el cliente de Secrets Manager de boto3."""
    def get_secret_value(self, SecretId):
        if SecretId == "prod/musepa/vercel/postgres":
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

class TestGetManagers(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.managers.get_managers.app.get_db_connection")
    @patch("modules.managers.get_managers.app.authorizate_user")
    @patch("modules.managers.get_managers.app.validate_connection")
    def test_get_managers_success(self, mock_validate_connection, mock_authorizate_user,mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Simular una validación exitosa
        simulate_valid_validations(mock_validate_connection)

        # Simular fetchall
        self.mock_cursor.fetchall.return_value = [
            {
                "id": 1,
                "name": "manager 1",
                "surname": "manager 1",
                "lastname": "manager 1",
                "phone_number": "7771112233",
                "address": "address",
                "birthdate": "1990-02-01",
                "id_user": 1,
                "id_museum": 1
            },
            {
                "id": 2,
                "name": "manager 2",
                "surname": "manager 2",
                "lastname": "manager 2",
                "phone_number": "7778889922",
                "address": "address",
                "birthdate": "1990-02-01",
                "id_user": 2,
                "id_museum": 1
            }
        ]

        self.mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "email": "user1@gmail.com",
                "password": "USER1",
                "username": "USER1",
                "id_role": 1
            },
            {
                "id": 2,
                "email": "user2@gmail.com",
                "password": "USRE2",
                "username": "USER2",
                "id_role": 1
            }
        ]

        # Ejecutar la función lambda_handle
        result = lambda_handler(None, None)

        # Imprimir el resultado
        print(result)

        self.assertEqual(result["statusCode"], 200)

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.managers.get_managers.app.get_db_connection")
    @patch("modules.managers.get_managers.app.authorizate_user")
    def test_lambda_invalid_conn(self, mock_authorizate_user,mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = None

        result = lambda_handler(None, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.managers.get_managers.app.get_db_connection")
    @patch("modules.managers.get_managers.app.authorizate_user")
    def test_lambda_handler_500_error(self, mock_authorizate_user, mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Simular excepción
        self.mock_cursor.execute.side_effect = Exception("Simulated database error")

        # Simular request
        result = lambda_handler(None, None)

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


class TestFunctions(TestCase):
    def test_datetime_serializer_datetime(self):
        dt = datetime(2023, 10, 26, 12, 34, 56)
        serialized = datetime_serializer(dt)
        self.assertEqual(serialized, "2023-10-26T12:34:56")

    def test_datetime_serializer_date(self):
        d = date(2023, 10, 26)
        datetime_serializer(d)

    def test_datetime_serializer_invalid_type(self):
        with self.assertRaisesRegex(TypeError, "Type <class 'str'> not serializable"):
            datetime_serializer("invalid")

class TestConnectDB(TestCase):
    @patch('modules.managers.get_managers.app.psycopg2.connect')
    @patch('modules.managers.get_managers.app.get_secrets')
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
                    raise ClientError(
                        {"Error": {"Code": "ResourceNotFoundException"}},
                        "get_secret_value"
                    )

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
