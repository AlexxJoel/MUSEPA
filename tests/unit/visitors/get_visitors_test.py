import json
import unittest
from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock

from modules.visitors.get_visitors.app import lambda_handler
from modules.visitors.get_visitors.functions import datetime_serializer
from modules.visitors.get_visitors.validations import validate_connection


def simulate_valid_validations(mock_validate_connection):
    mock_validate_connection.return_value = None


class TestGetVisitors(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.visitors.get_visitors.app.psycopg2.connect")
    @patch("modules.visitors.get_visitors.app.validate_connection")
    def test_get_visitors_success(self, mock_validate_connection, mock_psycopg2_connect):
        # Simular conexión
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simular una validación exitosa
        simulate_valid_validations(mock_validate_connection)

        # Simualar fetchall
        self.mock_cursor.fetchall.return_value = [
            {
                "id": 3,
                "name": "José",
                "surname": "Perez",
                "lastname": "Lopez",
                "favorites": [
                    1,
                    2
                ],
                "id_user": 10,
            }
        ]

        self.mock_cursor.fetchone.side_effect = [
            {
                "id": 10,
                "email": "jose@example.com",
                "password": "securepassword123",
                "username": "usuario",
                "id_role": 2
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

    @patch("modules.visitors.get_visitors.app.psycopg2.connect")
    def test_lambda_invalid_conn(self, mock_psycopg2_connect):
        # Simular conexión
        mock_psycopg2_connect.return_value = None

        # Simular una validación fallida
        event = {'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.visitors.get_visitors.app.psycopg2.connect")
    @patch("modules.visitors.get_visitors.app.validate_connection")
    def test_lambda_handler_500_error(self, mock_validate_connection, mock_psycopg2_connect):
        # Simular conexión
        mock_psycopg2_connect.return_value = self.mock_connection

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


if __name__ == '__main__':
    unittest.main()
