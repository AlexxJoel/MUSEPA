import json
from unittest import TestCase
from unittest.mock import patch, MagicMock

from modules.managers.find_manager.app import lambda_handler


class TestFindManager(TestCase):
    @patch("modules.managers.find_manager.app.psycopg2.connect")
    @patch("modules.managers.find_manager.app.validate_connection")
    @patch("modules.managers.find_manager.app.validate_event_path_params")
    def test_lambda_handler_500_error(self, mock_validate_event_path_params, mock_validate_connection,
                                      mock_psycopg2_connect):
        # Mock the connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simulate successful validations
        mock_validate_connection.return_value = None
        mock_validate_event_path_params.return_value = None

        # Simulate an exception when executing the SQL query
        mock_cursor.execute.side_effect = Exception("Simulated database error")

        # Create a test event
        event = {'pathParameters': {'id': '1'}}

        # Call the lambda_handler function
        result = lambda_handler(event, None)
        print(result)
        # Verify the result
        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Simulated database error"}))
