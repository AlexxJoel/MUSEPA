import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock

from modules.managers.create_manager.app import lambda_handler
from modules.managers.create_manager.validations import validate_connection, validate_event_body, validate_payload


def simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload):
    mock_validate_connection.return_value = None
    mock_validate_event_body.return_value = None
    mock_validate_payload.return_value = None


class TestCreateManager(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.managers.create_manager.app.psycopg2.connect")
    @patch("modules.managers.create_manager.app.validate_connection")
    @patch("modules.managers.create_manager.app.validate_event_body")
    @patch("modules.managers.create_manager.app.validate_payload")
    def test_create_manager_success(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                                    mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {
            'body': json.dumps({
                'email': 'example@example.com',
                'password': 'Test123.',
                'username': 'test',
                'name': 'test',
                'surname': 'test',
                'lastname': 'test',
                'phone_number': '7771112233',
                'address': 'test',
                'birthdate': '2000-01-01',
                'id_museum': '1'
            })
        }
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Manager created successfully"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()
        self.mock_connection.commit.assert_called_once()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.managers.create_manager.app.psycopg2.connect")
    def test_lambda_invalid_conn(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = None

        event = {'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.managers.create_manager.app.psycopg2.connect")
    @patch("modules.managers.create_manager.app.validate_connection")
    def test_lamda_invalid_event_body(self, mock_validate_connection, mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {}
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "No body provided."}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.managers.create_manager.app.psycopg2.connect")
    @patch("modules.managers.create_manager.app.validate_connection")
    @patch("modules.managers.create_manager.app.validate_event_body")
    def test_create_invalid_payload(self, mock_validate_event_body, mock_validate_connection,
                                    mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {
            'body': json.dumps({
                'password': 'Test123.',
                'username': 'test',
                'name': 'test',
                'surname': 'test',
                'lastname': 'test',
                'phone_number': '7771112233',
                'address': 'test',
                'birthdate': '2000-01-01',
                'id_museum': '1'
            })
        }

        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing 'email'"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.managers.create_manager.app.psycopg2.connect")
    @patch("modules.managers.create_manager.app.validate_connection")
    @patch("modules.managers.create_manager.app.validate_event_body")
    @patch("modules.managers.create_manager.app.validate_payload")
    def test_lambda_handler_500_error(self, mock_validate_payload, mock_validate_event_body,
                                      mock_validate_connection, mock_psycopg2_connect):
        # Simular conexión
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simular una validación exitosa
        simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload)

        # Simular excepción
        self.mock_cursor.execute.side_effect = Exception("Simulated database error")

        # Simular request
        event = {
            'body': json.dumps({
                'email': 'example@example.com',
                'password': 'Test123.',
                'username': 'test',
                'name': 'test',
                'surname': 'test',
                'lastname': 'test',
                'phone_number': '7771112233',
                'address': 'test',
                'birthdate': '2000-01-01',
                'id_museum': '1'
            })
        }
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Simulated database error"}))


class TestValidations(TestCase):
    def setUp(self):
        self.valid_payload = {
            "email": "test@example.com",
            "password": 12345,
            "username": "testuser",
            "name": "Test",
            "surname": "User",
            "lastname": "Example",
            "phone_number": "+1234567890",
            "address": "123 Test St",
            "birthdate": "1990-01-01",
            "id_museum": "1"
        }

    def test_validate_connection_success(self):
        conn = unittest.mock.MagicMock()
        result = validate_connection(conn)
        self.assertIsNone(result)

    def test_validate_connection_failure(self):
        conn = None
        result = validate_connection(conn)
        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    def test_validate_event_body_success(self):
        event = {'body': json.dumps({"key": "value"})}
        result = validate_event_body(event)
        self.assertIsNone(result)

    def test_validate_event_body_missing_body(self):
        event = {}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "No body provided."}))

    def test_validate_event_body_null_body(self):
        event = {'body': None}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body is null."}))

    def test_validate_event_body_empty_body(self):
        event = {'body': ""}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body is empty."}))

    def test_validate_event_body_body_as_list(self):
        event = {'body': []}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body can not be a list."}))

    def test_validate_event_body_invalid_json(self):
        event = {'body': "invalid json"}
        result = validate_event_body(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "The request body is not valid JSON"}))

    def test_validate_payload_valid(self):
        self.assertIsNone(validate_payload(self.valid_payload))

    def test_validate_payload_missing_email(self):
        payload = self.valid_payload.copy()
        del payload["email"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'email'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_email(self):
        payload = self.valid_payload.copy()
        payload["email"] = "invalidemail"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'email'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_password(self):
        payload = self.valid_payload.copy()
        del payload["password"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'password'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_password(self):
        payload = self.valid_payload.copy()
        payload["password"] = ["notastr"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'password'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_username(self):
        payload = self.valid_payload.copy()
        del payload["username"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'username'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_username(self):
        payload = self.valid_payload.copy()
        payload["username"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'username'"})}
        self.assertEqual(validate_payload(payload), expected_response)

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

    def test_validate_payload_missing_surname(self):
        payload = self.valid_payload.copy()
        del payload["surname"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'surname'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_surname(self):
        payload = self.valid_payload.copy()
        payload["surname"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'surname'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_lastname(self):
        payload = self.valid_payload.copy()
        del payload["lastname"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'lastname'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_lastname(self):
        payload = self.valid_payload.copy()
        payload["lastname"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'lastname'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_phone_number(self):
        payload = self.valid_payload.copy()
        del payload["phone_number"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'phone_number'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_phone_number(self):
        payload = self.valid_payload.copy()
        payload["phone_number"] = "invalidphone"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'phone_number'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_address(self):
        payload = self.valid_payload.copy()
        del payload["address"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'address'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_address(self):
        payload = self.valid_payload.copy()
        payload["address"] = "Invalid@123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'address'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_birthdate(self):
        payload = self.valid_payload.copy()
        del payload["birthdate"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'birthdate'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_birthdate(self):
        payload = self.valid_payload.copy()
        payload["birthdate"] = "01-01-1990"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'birthdate'"})}
        self.assertEqual(validate_payload(payload), expected_response)
    
    def test_validate_payload_missing_id_museum(self):
        payload = self.valid_payload.copy()
        del payload['id_museum']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id_museum'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_id_museum(self):
        payload = self.valid_payload.copy()
        payload['id_museum'] = 'CAMPOS'
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id_museum'"})}
        self.assertEqual(validate_payload(payload), expected_response)


if __name__ == '__main__':
    unittest.main()
