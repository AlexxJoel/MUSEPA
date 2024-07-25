import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from modules.visitors.find_visitor.app import lambda_handler
from modules.visitors.find_visitor.functions import datetime_serializer
from modules.visitors.find_visitor.validations import validate_connection, validate_event_path_params


def simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection):
    mock_validate_connection.return_value = None
    mock_validate_event_path_params.return_value = None


class TestFindVisitor(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.visitors.find_visitor.app.psycopg2.connect")
    @patch("modules.visitors.find_visitor.app.validate_connection")
    @patch("modules.visitors.find_visitor.app.validate_event_path_params")
    def test_find_visitor_success(self, mock_validate_event_path_params, mock_validate_connection,
                                  mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.side_effect = [
            {
                "id": 4,
                "name": "Pedro Luis",
                "surname": "Ken",
                "lastname": "Juz",
                "favorites": [2],
                "id_user": 11
            },
            {
                "id": 11,
                "email": "pedroact@example.com",
                "password": "aaaaaa",
                "username": "pedro2",
                "id_role": 2
            }
        ]

        event = {'pathParameters': {'id': '4'}}
        result = lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        expected_body = {
            "data": {
                "id": 4,
                "name": "Pedro Luis",
                "surname": "Ken",
                "lastname": "Juz",
                "favorites": [
                    2
                ],
                "id_user": 11,
                "user": {
                    "id": 11,
                    "email": "pedroact@example.com",
                    "password": "aaaaaa",
                    "username": "pedro2",
                    "id_role": 2
                }
            }
        }

        self.assertEqual(result["body"], json.dumps(expected_body))

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.visitors.find_visitor.app.psycopg2.connect")
    @patch("modules.visitors.find_visitor.app.validate_connection")
    @patch("modules.visitors.find_visitor.app.validate_event_path_params")
    def test_find_visitor_not_found(self, mock_validate_event_path_params, mock_validate_connection,
                                    mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.return_value = None

        event = {'pathParameters': {'id': '999'}}
        result = lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(result["body"], json.dumps({"error": "Visitor not found"}))

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.visitors.find_visitor.app.psycopg2.connect")
    @patch("modules.visitors.find_visitor.app.validate_connection")
    @patch("modules.visitors.find_visitor.app.validate_event_path_params")
    def test_find_user_not_found(self, mock_validate_event_path_params, mock_validate_connection,
                                 mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.side_effect = [
            {
                "id": 4,
                "name": "Pedro Luis",
                "surname": "Ken",
                "lastname": "Juz",
                "favorites": [2],
                "id_user": 11
            },
            None
        ]

        event = {'pathParameters': {'id': '999'}}
        result = lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(result["body"], json.dumps({"error": "User not found"}))

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.visitors.find_visitor.app.psycopg2.connect")
    def test_lambda_invalid_conn(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = None

        event = {'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.visitors.find_visitor.app.psycopg2.connect")
    def test_lambda_invalid_path_parameters(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = MagicMock()

        event = {'pathParameters': None}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 400)

    @patch("modules.visitors.find_visitor.app.psycopg2.connect")
    @patch("modules.visitors.find_visitor.app.validate_connection")
    @patch("modules.visitors.find_visitor.app.validate_event_path_params")
    def test_lambda_handler_500_error(self, mock_validate_event_path_params, mock_validate_connection,
                                      mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.execute.side_effect = Exception("Simulated database error")

        event = {'pathParameters': {'id': '1'}}
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
