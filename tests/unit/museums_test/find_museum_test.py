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

        self.mock_cursor.fetchone.side_effect = [
            {
                'name': 'Event Name',
                'location': 'Event Location',
                'tariffs': '100',
                'schedules': 'Event Schedules',
                'contact_number': '123-456-7890',
                'contact_email': 'contact@example.com',
                'id_owner': '1',
                'pictures': 'pic1'
            },
            {
                'id': '1',
                'name': 'John',
                'surname': 'Doe',
                'lastname': 'Smith',
                'phone_number': '+1234567890',
                'address': '123 Main St, Anytown, USA',
                'birthdate': '1990-01-01',
                'id_user': '1'
            }
        ],

