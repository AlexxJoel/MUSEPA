import json

from unittest import TestCase
import unittest
from unittest.mock import MagicMock, patch
from modules.museums.create_museum.app import lambda_handler
from modules.museums.create_museum.app import validate_connection, validate_event_body, validate_payload


def simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload):
    mock_validate_connection.return_value = None
    mock_validate_event_body.return_value = None
    mock_validate_payload.return_value = None


class TestCreateMuseum(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.museums.create_museum.app.psycopg2.connect")
    @patch("modules.museums.create_museum.app.validate_connection")
    @patch("modules.museums.create_museum.app.validate_event_body")
    @patch("modules.museums.create_museum.app.validate_payload")
    def test_create_museum_success(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                                   mock_psycopg2_connect):
        # Configure mocks for connect to pyscopg2
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simulate successful validations
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        # Run lambda handler with a mocked museum
        museum = {
            'body': json.dumps({
                'name': 'Event Name',
                'location': 'Event Location',
                'tariffs': 'Tariffs Information',
                'schedules': 'Event Schedules',
                'contact_number': '123-456-7890',
                'contact_email': 'contact@example.com',
                'pictures': 'pic1,pic2'
            })
        }

        result = lambda_handler(museum, None)

        # Print resul
        print(result)

        # Verify that the result is the same as the expected
        self.assertEqual(result['statusCode'], 200)
        self.assertEqual(json.loads(result['body']), {"message": "Museum created successfully"})

        # Verify that the close connection method was called correctly
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()
        self.mock_connection.commit.assert_called_once()
        self.mock_connection.rollback.assert_not_called()

    @patch('modules.museums.create_museum.app.psycopg2.connect')
    def test_lambda_invalid_connection(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = None

        museum = {
            'body': json.dumps({
                'name': 'Event Name',
                'location': 'Event Location',
                'tariffs': 'Tariffs Information',
                'schedules': 'Event Schedules',
                'contact_number': '123-456-7890',
                'contact_email': 'contact@example.com',
                'pictures': 'pic1,pic2'
            })
        }
        result = lambda_handler(museum, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(json.loads(result['body']), {"error": "Connection to the database failed"})

    @patch('modules.museums.create_museum.app.psycopg2.connect')
    @patch('modules.museums.create_museum.app.validate_connection')
    def test_lambda_invalid_event_body(self, mock_validate_connection, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        mock_validate_connection.return_value = None

        museum = {}
        result = lambda_handler(museum, None)

        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(json.loads(result['body']), {"error": "No body provided."})

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        self.mock_connection.rollback.assert_not_called()

    @patch('modules.museums.create_museum.app.psycopg2.connect')
    @patch('modules.museums.create_museum.app.validate_connection')
    @patch('modules.museums.create_museum.app.validate_event_body')
    def test_lambda_invalid_payload(self, mock_validate_event_body, mock_validate_connection, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None

        museum = {
            'body': json.dumps({
                'location': 'Event Location',
                'tariffs': 'Tariffs Information',
                'schedules': 'Event Schedules',
                'contact_number': '123-456-7890',
                'contact_email': 'contact@example.com',
                'pictures': 'pic1,pic2'})
        }

        result = lambda_handler(museum, None)

        print(result)

        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result['body'], json.dumps({"error": "Invalid or missing 'name'"}))

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        self.mock_connection.rollback.assert_not_called()

    @patch('modules.museums.create_museum.app.psycopg2.connect')
    @patch('modules.museums.create_museum.app.validate_connection')
    @patch('modules.museums.create_museum.app.validate_event_body')
    @patch('modules.museums.create_museum.app.validate_payload')
    def test_lambda_handler_500_error(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                                      mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection

        simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload)

        self.mock_cursor.execute.side_effect = Exception("Simulated database error")


        museum = {
            'body': json.dumps({
                'name': 'Event Name',
                'location': 'Event Location',
                'tariffs': 'Tariffs Information',
                'schedules': 'Event Schedules',
                'contact_number': '123-456-7890',
                'contact_email': 'contact@example.com',
                'pictures': 'pic1,pic2'})
        }

        result = lambda_handler(museum, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(json.loads(result['body']), {"error": "Simulated database error"})


class TestValidations(TestCase):
    def setUp(self):
        self.valid_payload = {
            'name': 'Event Name',
            'location': 'Event Location',
            'tariffs': '100',
            'schedules': 'Event Schedules',
            'contact_number': '123-456-7890',
            'contact_email': 'contact@example.com',
            'pictures': 'pic1'
        }



    def test_validate_connection_success(self):
        conn = unittest.mock.MagicMock()
        result = validate_connection(conn)
        self.assertIsNone(result)

    def test_validate_event_body_success(self):
        event = {'body': json.dumps(self.valid_payload)}
        result = validate_event_body(event)
        self.assertIsNone(result)

    def test_validate_event_body_missing_body(self):
        event = {}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result['body'], json.dumps({"error": "No body provided."}))

    def test_validate_event_body_null_body(self):
        event = {'body': None}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result['body'], json.dumps({"error": "Body is null."}))

    def test_validate_event_body_empty_body(self):
        event = {'body': ''}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result['body'], json.dumps({"error": "Body is empty."}))

    def test_validate_event_body_body_as_list(self):
        event = {'body': []}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body can not be a list."}))

    def test_validate_event_body_invalid_json(self):
        event = {'body': 'invalid json'}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result['body'], json.dumps({"error": "The request body is not valid JSON"}))

    # need update to be able
    def test_validate_payload_valid(self):
        self.assertIsNone(validate_payload(self.valid_payload))

    def test_validate_payloas_missing_name(self):
        payload = self.valid_payload.copy()
        del payload['name']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_name(self):
        payload = self.valid_payload.copy()
        payload['name'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"})}
        self.assertEqual(validate_payload(payload), expected_response)



    def test_validate_payload_missing_location(self):
        payload = self.valid_payload.copy()
        del payload['location']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'location'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_location(self):
        payload = self.valid_payload.copy()
        payload['location'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'location'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_tariffs(self):
        payload = self.valid_payload.copy()
        del payload['tariffs']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'tariffs'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_tariffs(self):
        payload = self.valid_payload.copy()
        payload['tariffs'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'tariffs'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_schedules(self):
        payload = self.valid_payload.copy()
        del payload['schedules']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'schedules'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_schedules(self):
        payload = self.valid_payload.copy()
        payload['schedules'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'schedules'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_contact_number(self):
        payload = self.valid_payload.copy()
        del payload['contact_number']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_number'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_contact_number(self):
        payload = self.valid_payload.copy()
        payload['contact_number'] = 'CAMPOS'
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_number'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_contact_email(self):
        payload = self.valid_payload.copy()
        del payload['contact_email']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_email'"})}
        self.assertEqual(validate_payload(payload), expected_response)


    def test_validate_payload_invalid_contact_email(self):
        payload = self.valid_payload.copy()
        payload['contact_email'] = 'invalidcontactemail'
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_email'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_pictures(self):
        payload = self.valid_payload.copy()
        del payload['pictures']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_pictures(self):
        payload = self.valid_payload.copy()
        payload['pictures'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"})}
        self.assertEqual(validate_payload(payload), expected_response)

if __name__ == '__main__':
    unittest.main()
