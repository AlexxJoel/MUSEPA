import json
import unittest
from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock
import boto3
from botocore.exceptions import ClientError
import jwt

from modules.visitors.get_visitors.app import lambda_handler
from modules.visitors.get_visitors.functions import datetime_serializer
from modules.visitors.get_visitors.validations import validate_connection
from modules.visitors.get_visitors.connect_db import get_db_connection,get_secrets
from modules.visitors.get_visitors.authorization import authorizate_user


def simulate_valid_validations(mock_validate_connection):
    mock_validate_connection.return_value = None

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

class TestGetVisitors(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.visitors.get_visitors.app.get_db_connection")
    @patch("modules.visitors.get_visitors.app.authorizate_user")
    @patch("modules.visitors.get_visitors.app.validate_connection")
    def test_get_visitors_success(self, mock_validate_connection, mock_authorizate_user, mock_get_db_connection):
        # Simular la autorización y la conexión DB
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None

        # Simular fetchall para obtener usuarios
        self.mock_cursor.fetchall.return_value = [
            {
                "id": 10,
                "email": "jose@example.com",
                "password": "securepassword123",
                "username": "usuario",
                "id_role": 2
            }
        ]

        # Simular fetchone para obtener un visitante
        self.mock_cursor.fetchone.return_value = {
            "id": 3,
            "name": "José",
            "surname": "Perez",
            "lastname": "Lopez",
            "favorites": [1, 2],
            "id_user": 10,
        }

        # Ejecutar la función lambda_handler
        result = lambda_handler(None, None)

        # Imprimir el resultado (solo para depuración, eliminar en producción)
        print(result)

        # Verificar que el resultado es el esperado
        self.assertEqual(result["statusCode"], 200)
        expected_body = {
            "data": [
                {
                    "id": 3,
                    "name": "José",
                    "surname": "Perez",
                    "lastname": "Lopez",
                    "favorites": [1, 2],
                    "id_user": 10,
                    "user": {
                        "id": 10,
                        "email": "jose@example.com",
                        "password": "securepassword123",
                        "username": "usuario",
                        "id_role": 2
                    }
                }
            ]
        }
        self.assertEqual(json.loads(result["body"]), expected_body)

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.visitors.get_visitors.app.get_db_connection")
    @patch("modules.visitors.get_visitors.app.authorizate_user")
    def test_lambda_invalid_conn(self, mock_authorizate_user, mock_get_db_connection):
        # Simular la autorización y la conexión DB
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = None

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular una validación fallida
        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.visitors.get_visitors.app.get_db_connection")
    @patch("modules.visitors.get_visitors.app.authorizate_user")
    @patch("modules.visitors.get_visitors.app.validate_connection")
    def test_lambda_handler_500_error(self, mock_validate_connection, mock_authorizate_user, mock_get_db_connection):
        # Simular la autorización y la conexión DB
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Simular una validación exitosa
        simulate_valid_validations(mock_validate_connection)

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
    @patch('modules.visitors.get_visitors.connect_db.psycopg2.connect')
    @patch('modules.visitors.get_visitors.connect_db.get_secrets')
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
