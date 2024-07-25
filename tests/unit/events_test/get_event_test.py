import json
import unittest
from unittest import TestCase
from datetime import date, datetime
from unittest.mock import patch, MagicMock
from modules.events.get_events.app import lambda_handler
from modules.events.get_events.validations import validate_connection
from modules.events.get_events.functions import datetime_serializer

def simulate_valid_validations(mock_validate_connection):
    mock_validate_connection.return_value = None

class MyTestCase(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.events.get_events.app.psycopg2.connect")
    @patch("modules.events.get_events.app.validate_connection")
    def test_get_events_success(self, mock_validate_connection, mock_psycopg2_connect):
        # Simular conexión
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simular una validación exitosa
        simulate_valid_validations(mock_validate_connection)

        # Simular resultado de la consulta
        self.mock_cursor.fetchall.return_value = [
            {"id": 1, "name": "Event 1", "date": "2023-01-01T00:00:00"},
            {"id": 2, "name": "Event 2", "date": "2023-02-01T00:00:00"}
        ]

        # Ejecutar la función lambda_handle
        result = lambda_handler(None,None)

        # Imprimir el resultado
        print(result)

        self.assertEqual(result["statusCode"], 200)
        self.assertIn("data", json.loads(result["body"]))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.events.get_events.app.psycopg2.connect")
    @patch("modules.events.get_events.app.validate_connection")
    def test_get_events_failed_validation(self, mock_validate_connection, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        mock_validate_connection.return_value = {'statusCode': 400, 'body': json.dumps('Invalid connection')}

        result = lambda_handler(None, None)

        print(result)

        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps('Invalid connection'))

    @patch("modules.events.get_events.app.psycopg2.connect")
    @patch("modules.events.get_events.app.validate_connection")
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

if __name__ == "__main__":
    unittest.main()
