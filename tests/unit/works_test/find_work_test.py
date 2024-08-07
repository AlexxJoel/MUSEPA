import json
from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock
from modules.works.find_work.app import lambda_handler
from modules.works.find_work.functions import datetime_serializer
from modules.works.find_work.validations import validate_connection, validate_event_path_params
from datetime import datetime, date


def simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection):
    mock_validate_connection.return_value = None
    mock_validate_event_path_params.return_value = None


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


if __name__ == "__main__":
    unittest.main()
