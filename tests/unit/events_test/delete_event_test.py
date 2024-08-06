import json
from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock

import jwt

from modules.events.delete_event.app import lambda_handler
from modules.events.delete_event.validations import validate_connection,validate_event_path_params


def simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection):
    mock_validate_connection.return_value = None
    mock_validate_event_path_params.return_value = None

class TestDeleteEvent(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.events.delete_event.app.get_db_connection")
    @patch("modules.events.delete_event.app.authorizate_user")
    @patch("modules.events.delete_event.app.validate_connection")
    @patch("modules.events.delete_event.app.validate_event_path_params")
    def test_delete_event_success(self, mock_validate_event_path_params, mock_validate_connection, mock_authorizate_user,
                                  mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)
        self.mock_cursor.fetchone.return_value = {'id': 1}

        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        print(result)

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Event deleted successfully"}))
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.events.delete_event.app.get_db_connection")
    @patch("modules.events.delete_event.app.authorizate_user")
    @patch("modules.events.delete_event.app.validate_connection")
    @patch("modules.events.delete_event.app.validate_event_path_params")
    def test_delete_event_not_found(self, mock_validate_event_path_params, mock_validate_connection, mock_authorizate_user,mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.return_value = None

        event = { 'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '999'}}
        result = lambda_handler(event, None)

        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(result["body"], json.dumps({"error": "Event not found"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.events.delete_event.app.get_db_connection")
    @patch("modules.events.delete_event.app.authorizate_user")
    def test_lambda_invalid_conn(self, mock_authorizate_user,mock_get_db_connection):
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

    @patch("modules.events.delete_event.app.get_db_connection")
    @patch("modules.events.delete_event.app.authorizate_user")
    def test_lambda_invalid_path_parameters(self, mock_authorizate_user,mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        event = {'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': None}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 400)

    @patch("modules.events.delete_event.app.get_db_connection")
    @patch("modules.events.delete_event.app.authorizate_user")
    @patch("modules.events.delete_event.app.validate_connection")
    @patch("modules.events.delete_event.app.validate_event_path_params")
    def test_lambda_handler_500_error(self, mock_validate_event_path_params, mock_validate_connection,
                                      mock_authorizate_user, mock_get_db_connection):
        # Simular una autorización exitosa
        mock_authorizate_user.return_value = None

        # Configurar el mock de conexión a la base de datos
        mock_connection = MagicMock()
        mock_get_db_connection.return_value = mock_connection
        mock_cursor = mock_connection.cursor.return_value

        # Simular validaciones exitosas
        mock_validate_connection.return_value = None
        mock_validate_event_path_params.return_value = None

        # Simular una excepción durante la ejecución de la consulta
        mock_cursor.execute.side_effect = Exception("Simulated database error")

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Crear un evento de prueba
        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}
        }

        # Ejecutar la función lambda_handler
        result = lambda_handler(event, None)

        # Verificar el resultado del error de la base de datos
        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"message": "Simulated database error"}))

        # Verificar que los métodos de cierre se llamen correctamente
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()


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
        self.assertEqual(result["body"], json.dumps({"error": "Path parameters is missing from the request."}))

    def test_validate_event_path_params_null_path_parameters(self):
        event = {'pathParameters': None}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Path parameters is null."}))

    def test_validate_event_path_params_missing_id(self):
        event = {'pathParameters': {}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID is missing from the path parameters."}))

    def test_validate_event_path_params_null_id(self):
        event = {'pathParameters': {'id': None}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID is missing from the path parameters."}))

    def test_validate_event_path_params_invalid_id_type(self):
        event = {'pathParameters': {'id': 'abc'}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID data type is wrong."}))

    def test_validate_event_path_params_invalid_id_value(self):
        event = {'pathParameters': {'id': '0'}}
        result = validate_event_path_params(event)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Request ID invalid value."}))



if __name__ == "__main__":
    unittest.main()
