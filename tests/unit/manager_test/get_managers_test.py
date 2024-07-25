import json
import unittest
from datetime import date, datetime
from unittest import TestCase
from unittest.mock import patch, MagicMock

from modules.managers.get_managers.app import lambda_handler
from modules.managers.get_managers.functions import datetime_serializer
from modules.managers.get_managers.validations import validate_connection


def simulate_valid_validations(mock_validate_connection):
    mock_validate_connection.return_value = None


class TestGetManagers(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.managers.get_managers.app.psycopg2.connect")
    @patch("modules.managers.get_managers.app.validate_connection")
    def test_get_managers_success(self, mock_validate_connection, mock_psycopg2_connect):
        # Simular conexión
        mock_psycopg2_connect.return_value = self.mock_connection

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

    @patch("modules.managers.get_managers.app.psycopg2.connect")
    def test_lambda_invalid_conn(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = None

        result = lambda_handler(None, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.managers.get_managers.app.psycopg2.connect")
    @patch("modules.managers.get_managers.app.validate_connection")
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
