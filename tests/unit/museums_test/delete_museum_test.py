import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock

from modules.museums.delete_museum.app import lambda_handler
from modules.museums.delete_museum.validations import validate_connection, validate_event_path_params

def simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection):
    mock_validate_event_path_params.return_value = None
    mock_validate_connection.return_value = None


class TestFindMuseum(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.museums.delete_museum.app.psycopg2.connect")
    @patch("modules.museums.delete_museum.app.validate_connection")
    @patch("modules.museums.delete_museum.app.validate_event_path_params")
    def test_delete_museum_success(self, mock_validate_event_path_params, mock_validate_connection, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.return_value = {'id': 1}

        event = {'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)


        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Museum deleted successfully"}))
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()


    @patch("modules.museums.delete_museum.app.psycopg2.connect")
    @patch("modules.museums.delete_museum.app.validate_connection")
    @patch("modules.museums.delete_museum.app.validate_event_path_params")
    def test_find_manager_not_found(self, mock_validate_event_path_params, mock_validate_connection, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.return_value = None

        event = {'pathParameters': {'id': '999'}}
        result = lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Museum not found"}))

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.museums.delete_museum.app.psycopg2.connect")
    def test_lambda_invalid_conn(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = None

        event = {'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))


    @patch("modules.museums.delete_museum.app.psycopg2.connect")
    def test_lambda_invalid_path_parameters(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = MagicMock()

        event = {'pathParameters': None}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 400)

    @patch("modules.museums.delete_museum.app.psycopg2.connect")
    @patch("modules.museums.delete_museum.app.validate_connection")
    @patch("modules.museums.delete_museum.app.validate_event_path_params")
    def test_lambda_handler_500_error(self, mock_validate_event_path_params, mock_validate_connection,
                                      mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.execute.side_effect = Exception("Simulated database error")

        event = {'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"message": "Simulated database error"}))



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

    def test_validate_event_path_params_null_id(self):
        event = {'pathParameters': {'id': None}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID is missing from the path parameters."}))

    def test_validate_event_path_params_invalid_id(self):
        event = {'pathParameters': {'id': 'abc'}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID data type is wrong."}))

    def test_validate_event_path_params_invalid_id_value(self):
        event = {'pathParameters': {'id': '0'}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID invalid value."}))

if __name__ == '__main__':
    unittest.main()