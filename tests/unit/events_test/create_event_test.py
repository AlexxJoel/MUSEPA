import json
from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock
from modules.events.create_event.app import lambda_handler
from modules.events.create_event.app import validate_connection, validate_event_body, validate_payload

class TestCreateEvent(TestCase):

    @patch("modules.events.create_event.app.psycopg2.connect")
    @patch("modules.events.create_event.app.validate_connection")
    @patch("modules.events.create_event.app.validate_event_body")
    @patch("modules.events.create_event.app.validate_payload")
    def test_lambda_handler_500_error(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection, mock_psycopg2_connect):
        # Mock the connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simulate successful validations
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        # Simulate an exception when executing the SQL query
        mock_cursor.execute.side_effect = Exception("Simulated database error")

        # Create a test event
        event = {
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

        # Call the lambda_handler function
        result = lambda_handler(event, None)
        print(result)
        # Verify the result
        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Simulated database error"}))

        # Verify that rollback was called
        mock_connection.rollback.assert_called_once()

        # Verify that connection and cursor were closed
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()

    @patch("modules.events.create_event.app.psycopg2.connect")
    @patch("modules.events.create_event.app.validate_connection")
    @patch("modules.events.create_event.app.validate_event_body")
    @patch("modules.events.create_event.app.validate_payload")
    def test_create_event_success(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection, mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {
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
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_connection.commit.assert_called_once()
        mock_connection.rollback.assert_not_called()

    @patch("modules.events.create_event.app.psycopg2.connect")
    @patch("modules.events.create_event.app.validate_connection")
    @patch("modules.events.create_event.app.validate_event_body")
    @patch("modules.events.create_event.app.validate_payload")
    def test_create_event_invalid_payload(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection, mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None

        # Simular una carga útil inválida
        mock_validate_payload.return_value = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing name"})}

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {
            'body': json.dumps({
                'name': '',
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
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing name"}))

        # Verificar que no se ha llamado a commit o rollback
        mock_connection.commit.assert_not_called()
        mock_connection.rollback.assert_not_called()

    @patch("modules.events.create_event.app.psycopg2.connect")
    def test_validate_connection_failure(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = None
        result = validate_connection(mock_psycopg2_connect.return_value)
        self.assertEqual(result["statusCode"], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

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
        self.assertEqual(result["body"], json.dumps({"error": "Body is empty."}))

    def test_validate_event_body_invalid_json(self):
        event = {"body": "{invalid: json}"}
        result = validate_event_body(event)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "The request body is not valid JSON"}))

    def test_validate_payload_missing_name(self):
        payload = {
            "description": "Description 1",
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "category": "Category 1",
            "pictures": "pic1,pic2",
            "id_museum": "1"
        }
        result = validate_payload(payload)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing"}))

    def test_validate_payload_invalid_dates(self):
        payload = {
            "name": "Event 1",
            "description": "Description 1",
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "category": "Category 1",
            "pictures": "pic1,pic2",
            "id_museum": "1"
        }
        payload["start_date"] = "invalid_date"
        result = validate_payload(payload)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing"}))

        payload["start_date"] = "2024-01-01"
        payload["end_date"] = "invalid_date"
        result = validate_payload(payload)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing"}))

    def test_validate_payload_missing_field(self):
        payload = {
            "name": "Event 1",
            "description": "Description 1",
            "start_date": "2024-01-01",
            "end_date": "2024-01-02",
            "category": "Category 1",
            "pictures": "pic1,pic2"
        }
        result = validate_payload(payload)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing"}))


if __name__ == "__main__":
    unittest.main()
