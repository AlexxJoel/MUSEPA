import json
from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock
import jwt

from modules.events.create_event.app import lambda_handler
from modules.events.create_event.app import validate_connection, validate_event_body, validate_payload

def simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload):
    mock_validate_connection.return_value = None
    mock_validate_event_body.return_value = None
    mock_validate_payload.return_value = None
class TestCreateEvent(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.events.create_event.app.get_db_connection")
    @patch("modules.events.create_event.app.authorizate_user")
    @patch("modules.events.create_event.app.validate_connection")
    @patch("modules.events.create_event.app.validate_event_body")
    @patch("modules.events.create_event.app.validate_payload")
    def test_create_event_success(self,mock_authorizate_user, mock_validate_payload, mock_validate_event_body, mock_validate_connection, mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None


        # Ejecutar la función lambda_handler con un evento de prueba
        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'name': 'Event 1',
                'description': 'Description 1',
                'start_date': '2024-01-01',
                'end_date': '2024-01-02',
                'category': 'Category 1',
                'pictures': 'pic1,pic2',
                'id_museum': '1'
            })
        }
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Event created successfully"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()
        self.mock_connection.commit.assert_called_once()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.events.create_event.app.get_db_connection")
    @patch("modules.events.create_event.app.authorizate_user")
    def test_lambda_invalid_conn(self, mock_get_db_connection,mock_authorizate_user):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = None

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        event = {'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.events.create_event.app.get_db_connection")
    @patch("modules.events.create_event.app.authorizate_user")
    @patch("modules.events.create_event.app.validate_connection")
    def test_lambda_invalid_event_body(self, mock_validate_connection, mock_get_db_connection, mock_authorizate_user):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = None

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular una validación exitosa
        mock_validate_connection.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {'headers': {
            'Authorization': f'Bearer {token}'
        }}
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "No body provided."}))

    @patch("modules.events.create_event.app.get_db_connection")
    @patch("modules.events.create_event.app.authorizate_user")
    @patch("modules.events.create_event.app.validate_connection")
    @patch("modules.events.create_event.app.validate_event_body")
    def test_create_event_invalid_payload(self, mock_validate_event_body, mock_validate_connection, mock_authorizate_user,mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'description': 'Description 1',
                'start_date': '2024-01-01',
                'end_date': '2024-01-02',
                'category': 'Category 1',
                'pictures': 'pic1,pic2',
                'id_museum': '1'
            })
        }
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing 'name'"}))

        # Verificar que no se ha llamado a commit o rollback
        self.mock_connection.commit.assert_not_called()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.events.create_event.app.get_db_connection")
    @patch("modules.events.create_event.app.authorizate_user")
    @patch("modules.events.create_event.app.validate_connection")
    @patch("modules.events.create_event.app.validate_event_body")
    @patch("modules.events.create_event.app.validate_payload")
    def test_lambda_handler_500_error(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                                      mock_authorizate_user, mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = MagicMock()
        mock_connection = mock_get_db_connection.return_value
        mock_cursor = mock_connection.cursor.return_value

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simulate successful validations
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        # Simulate an exception when executing the SQL query
        mock_cursor.execute.side_effect = Exception("Simulated database error")

        # Create a test event
        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'name': 'Event 1',
                'description': 'Description 1',
                'start_date': '2024-01-01',
                'end_date': '2024-01-02',
                'category': 'Category 1',
                'pictures': 'pic1,pic2',
                'id_museum': '1'
            })
        }

        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(json.loads(result['body'])["error"], "Simulated database error")

class TestValidations(TestCase):
    def setUp(self):
        self.valid_payload = {
            'name': 'aaaa',
            'description': 'eliminate',
            'start_date': '2024-01-01',
            'end_date': '2024-01-02',
            'category': 'Category',
            'pictures': 'pic1,pic2',
            'id_museum': '1'
        }

    @patch("modules.events.create_event.app.get_db_connection")
    def test_validate_connection_failure(self, mock_get_db_connection):
        mock_get_db_connection.return_value = None
        result = validate_connection(mock_get_db_connection.return_value)
        self.assertEqual(result["statusCode"], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))


    def test_validate_connection_success(self):
        conn = unittest.mock.MagicMock()
        result = validate_connection(conn)
        self.assertIsNone(result)

    def test_validate_event_body_success(self):
        event = {'body': json.dumps({"key": "value"})}
        result = validate_event_body(event)
        self.assertIsNone(result)

    def test_validate_event_body_no_body(self):
        event = {}
        result = validate_event_body(event)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "No body provided."}))

    def test_validate_event_body_null_body(self):
        event = {"body": None}
        result = validate_event_body(event)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body is null."}))

    def test_validate_event_body_empty_body(self):
        event = {"body": ""}
        result = validate_event_body(event)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body is empty."}))

    def test_validate_event_body_body_is_list(self):
        event = {"body": []}
        result = validate_event_body(event)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body can not be a list."}))

    def test_validate_event_body_invalid_json(self):
        event = {'body': "invalid json"}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "The request body is not valid JSON"}))

    def test_validate_payload_valid(self):
        self.assertIsNone(validate_payload(self.valid_payload))

    def test_validate_payload_missing_name(self):
        payload = self.valid_payload.copy()
        del payload["name"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_name(self):
        payload = self.valid_payload.copy()
        payload["name"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_description(self):
        payload = self.valid_payload.copy()
        del payload['description']

        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'description'"})}

        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_description(self):
        payload = self.valid_payload.copy()
        payload["description"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'description'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_start_date(self):
        payload = self.valid_payload.copy()
        del payload['start_date']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'start_date'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_start_date(self):
        payload = self.valid_payload.copy()
        payload["start_date"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'start_date'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_end_date(self):
        payload = self.valid_payload.copy()
        del payload['end_date']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'end_date'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_end_date(self):
        payload = self.valid_payload.copy()
        payload["end_date"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'end_date'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_category(self):
        payload = self.valid_payload.copy()
        del payload['category']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'category'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_category(self):
        payload = self.valid_payload.copy()
        payload["category"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'category'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_pictures(self):
        payload = self.valid_payload.copy()
        del payload['pictures']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_id_museum(self):
        payload = self.valid_payload.copy()
        del payload['id_museum']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id_museum'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_id_museum(self):
        payload = self.valid_payload.copy()
        payload["id_museum"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id_museum'"})}
        self.assertEqual(validate_payload(payload), expected_response)

if __name__ == "__main__":
    unittest.main()
