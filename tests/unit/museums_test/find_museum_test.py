import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
import boto3
from botocore.exceptions import ClientError


from modules.museums.find_museum.app import lambda_handler
from modules.museums.find_museum.connect_db import get_db_connection,get_secrets

def simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection):
    mock_validate_connection.return_value = None
    mock_validate_event_path_params.return_value = None

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

class TestFindMuseum(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.museums.find_museum.app.get_db_connection")
    @patch("modules.museums.find_museum.app.validate_connection")
    @patch("modules.museums.find_museum.app.validate_event_path_params")
    def test_find_museum_success(self, mock_validate_event_path_params, mock_validate_connection,
                                  mock_get_db_connection):
        mock_get_db_connection.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.return_value = {
            "id": 1,
            "name": "MUSEEPA",
            "location": None,
            "tariffs": None,
            "schedules": None,
            "contact_number": None,
            "contact_email": None,
            "pictures": None,
        }

        event = {'pathParameters': {'id': 1}}
        result = lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        expected_body = {
            "data": {
                "id": 1,
                "name": "MUSEEPA",
                "location": None,
                "tariffs": None,
                "schedules": None,
                "contact_number": None,
                "contact_email": None,
                "pictures": None
            }
        }

        self.assertEqual(json.loads(result["body"]), expected_body)
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

class TestConnectDB(TestCase):
    @patch('modules.museums.find_museum.connect_db.psycopg2.connect')
    @patch('modules.museums.find_museum.connect_db.get_secrets')
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


if __name__ == '__main__':
    unittest.main()
