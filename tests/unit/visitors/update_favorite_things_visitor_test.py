import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock

from modules.visitors.update_favorites_visitor.app import lambda_handler
from modules.visitors.update_favorites_visitor.validations import validate_connection, validate_event_body, \
    validate_payload


def simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload):
    mock_validate_connection.return_value = None
    mock_validate_event_body.return_value = None
    mock_validate_payload.return_value = None


class TestUpdateThingsVisitor(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.visitors.update_favorites_visitor.app.psycopg2.connect")
    @patch("modules.visitors.update_favorites_visitor.app.validate_connection")
    @patch("modules.visitors.update_favorites_visitor.app.validate_event_body")
    @patch("modules.visitors.update_favorites_visitor.app.validate_payload")
    def test_update_things_visitor_success(self, mock_validate_payload, mock_validate_event_body,
                                           mock_validate_connection,
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
                'id': 3,
                'favorites': [4, 3, 1]
            })
        }
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Favorites updated successfully"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()
        self.mock_connection.commit.assert_called_once()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.visitors.update_favorites_visitor.app.psycopg2.connect")
    @patch("modules.visitors.update_favorites_visitor.app.validate_connection")
    @patch("modules.visitors.update_favorites_visitor.app.validate_event_body")
    @patch("modules.visitors.update_favorites_visitor.app.validate_payload")
    def test_visitor_not_found(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                               mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        self.mock_cursor.fetchone.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {
            'body': json.dumps({
                'id': 3,
                'favorites': [4, 3, 1]
            })
        }
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(result["body"], json.dumps({"error": "Visitor not found"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()
        self.mock_connection.commit.assert_not_called()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.visitors.update_favorites_visitor.app.psycopg2.connect")
    def test_lambda_invalid_conn(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = None

        event = {
            'body': json.dumps({
                'id': 3,
                'favorites': [4, 3, 1]
            })
        }

        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.visitors.update_favorites_visitor.app.psycopg2.connect")
    @patch("modules.visitors.update_favorites_visitor.app.validate_connection")
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

    @patch("modules.visitors.update_favorites_visitor.app.psycopg2.connect")
    @patch("modules.visitors.update_favorites_visitor.app.validate_connection")
    @patch("modules.visitors.update_favorites_visitor.app.validate_event_body")
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
                'id': '3',
                'favorites': 1
            })
        }
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing 'favorites'"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.visitors.update_favorites_visitor.app.psycopg2.connect")
    @patch("modules.visitors.update_favorites_visitor.app.validate_connection")
    @patch("modules.visitors.update_favorites_visitor.app.validate_event_body")
    @patch("modules.visitors.update_favorites_visitor.app.validate_payload")
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
                'id': 3,
                'favorites': [4, 3, 1]
            })
        }
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Simulated database error"}))


class TestValidations(TestCase):
    def setUp(self):
        self.valid_payload = {
            'id': '3',
            'favorites': [4, 3, 1]
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

    def test_validate_payload_missing_id(self):
        payload = self.valid_payload.copy()
        del payload["id"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id'"})}
        self.assertEqual(validate_payload(payload), expected_response)


    def test_validate_payload_missing_username(self):
        payload = self.valid_payload.copy()
        del payload["favorites"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'favorites'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_username(self):
        payload = self.valid_payload.copy()
        payload["favorites"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'favorites'"})}


if __name__ == '__main__':
    unittest.main()
