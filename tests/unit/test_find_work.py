import json
from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock
import boto3
from botocore.exceptions import ClientError
from modules.works.find_work.app import lambda_handler
from modules.works.find_work.app import datetime_serializer
from modules.works.find_work.app import validate_connection, validate_event_path_params
from modules.works.find_work.app import get_db_connection,get_secrets
from datetime import datetime, date


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

class TestFindEvent(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.works.find_work.app.get_db_connection")
    @patch("modules.works.find_work.app.validate_connection")
    @patch("modules.works.find_work.app.validate_event_path_params")
    def test_find_event_success(self, mock_validate_event_path_params, mock_validate_connection, mock_get_db_connection):
        mock_get_db_connection.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.return_value = {
            'id': 1,
            'title': 'Title 1',
            'description': 'Description 1',
            'creation_date': '2024-01-01',
            'technique': 'puntos',
            'artist': 'more',
            'id_museum': '1',
            'pictures': 'pic1,pic2'
        }

        work = {'pathParameters': {'id': '1'}}
        result = lambda_handler(work, None)

        self.assertEqual(result["statusCode"], 200)
        expected_body = {
            "data": {
                'id': 1,
                'title': 'Title 1',
                'description': 'Description 1',
                'creation_date': '2024-01-01',
                'technique': 'puntos',
                'artist': 'more',
                'id_museum': '1',
                'pictures': 'pic1,pic2'
            }
        }
        self.assertEqual(result["body"], json.dumps(expected_body))
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.works.find_work.app.get_db_connection")
    @patch("modules.works.find_work.app.validate_connection")
    @patch("modules.works.find_work.app.validate_event_path_params")
    def test_find_event_not_found(self, mock_validate_event_path_params, mock_validate_connection,
                                  mock_get_db_connection):
        mock_get_db_connection.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.return_value = None

        work = {'pathParameters': {'id': '999'}}
        result = lambda_handler(work, None)

        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(result["body"], json.dumps({"error": "Work not found"}))

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.works.find_work.app.get_db_connection")
    def test_lambda_invalid_conn(self, mock_get_db_connection):
        mock_get_db_connection.return_value = None

        work = {'pathParameters': {'id': '1'}}
        result = lambda_handler(work, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.works.find_work.app.get_db_connection")
    def test_lambda_invalid_path_parameters(self, mock_get_db_connection):
        mock_get_db_connection.return_value = self.mock_connection

        work = {'pathParameters': None}
        result = lambda_handler(work, None)

        self.assertEqual(result['statusCode'], 400)

    @patch("modules.works.find_work.app.get_db_connection")
    @patch("modules.works.find_work.app.validate_connection")
    @patch("modules.works.find_work.app.validate_event_path_params")
    def test_lambda_handler_500_error(self, mock_validate_event_path_params, mock_validate_connection,
                                      mock_get_db_connection):
        mock_get_db_connection.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.execute.side_effect = Exception("Simulated database error")

        work = {'pathParameters': {'id': '1'}}
        result = lambda_handler(work, None)

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
        work = {'pathParameters': {'id': '7'}}
        result = validate_event_path_params(work)
        self.assertIsNone(result)

    def test_validate_event_path_params_missing_path_parameters(self):
        work = {}
        result = validate_event_path_params(work)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Path parameters is missing from the request."}))

    def test_validate_event_path_params_null_path_parameters(self):
        work = {'pathParameters': None}
        result = validate_event_path_params(work)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Path parameters is null."}))

    def test_validate_event_path_params_missing_id(self):
        work = {'pathParameters': {}}
        result = validate_event_path_params(work)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID is missing from the path parameters."}))

    def test_validate_event_path_params_null_id(self):
        work = {'pathParameters': {'id': None}}
        result = validate_event_path_params(work)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID is missing from the path parameters."}))

    def test_validate_event_path_params_invalid_id_type(self):
        work = {'pathParameters': {'id': 'abc'}}
        result = validate_event_path_params(work)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID data type is wrong."}))

    def test_validate_event_path_params_invalid_id_value(self):
        work = {'pathParameters': {'id': '0'}}
        result = validate_event_path_params(work)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID invalid value."}))


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
    @patch('modules.works.find_work.app.psycopg2.connect')
    @patch('modules.works.find_work.app.get_secrets')
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



if __name__ == "__main__":
    unittest.main()
