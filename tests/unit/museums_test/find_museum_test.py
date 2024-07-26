import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
from datetime import datetime, date

from modules.museums.find_museum.app import lambda_handler
from modules.museums.find_museum.functions import datetime_serializer
from modules.museums.find_museum.validations import validate_connection, validate_event_path_params


def simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection):
    mock_validate_connection.return_value = None
    mock_validate_event_path_params.return_value = None


class TestFindMuseum(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.museums.find_museum.app.psycopg2.connect")
    @patch("modules.museums.find_museum.app.validate_connection")
    @patch("modules.museums.find_museum.app.validate_event_path_params")
    def test_find_museum_success(self, mock_validate_event_path_params, mock_validate_connection,
                                 mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
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


if __name__ == '__main__':
    unittest.main()
