import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock

import jwt

from modules.managers.delete_manager.app import lambda_handler
from modules.managers.delete_manager.validations import validate_connection, validate_event_path_params


def simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection):
    mock_validate_connection.return_value = None
    mock_validate_event_path_params.return_value = None


class TestFindManager(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    @patch("modules.managers.delete_manager.app.validate_connection")
    @patch("modules.managers.delete_manager.app.validate_event_path_params")
    @patch("boto3.client")
    def test_delete_manager_success(self, mock_boto_client, mock_validate_event_path_params, mock_validate_connection,
                                    mock_authorizate_user, mock_get_db_connection):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        # Simula los datos devueltos por el cursor de la base de datos
        self.mock_cursor.fetchone.side_effect = [
            {
                "id": 1,
                "name": "Alejandro",
                "surname": "Morellano",
                "lastname": "Alvarez",
                "phone_number": "+1234567870",
                "address": "123 Main St, Anytoiwn, USA",
                "birthdate": "1990-02-01",
                "id_user": 18,
                'id_museum': 1
            },
            {
                "username": "alejandro.morellano"
            }
        ]

        # Simula la eliminación en Cognito
        mock_cognito_client = MagicMock()
        mock_boto_client.return_value = mock_cognito_client
        mock_cognito_client.admin_delete_user.return_value = {}

        # Simula el evento Lambda
        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}
        }
        result = lambda_handler(event, None)

        # Verifica que el resultado sea el esperado
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Manager deleted successfully"}))

        # Verifica que las conexiones y cursores se cierren correctamente
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    @patch("modules.managers.delete_manager.app.validate_connection")
    @patch("modules.managers.delete_manager.app.validate_event_path_params")
    def test_find_manager_not_found(self, mock_validate_event_path_params, mock_validate_connection,
                                    mock_authorizate_user, mock_get_db_connection):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.fetchone.return_value = None

        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '999'}}
        result = lambda_handler(event, None)

        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(result["body"], json.dumps({"error": "Manager not found"}))

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    def test_lambda_invalid_conn(self,  mock_authorizate_user, mock_get_db_connection):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = None

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        event = { 'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    def test_lambda_invalid_path_parameters(self,  mock_authorizate_user, mock_get_db_connection):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        event = {'pathParameters': None}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 400)

    @patch("modules.managers.delete_manager.app.get_db_connection")
    @patch("modules.managers.delete_manager.app.authorizate_user")
    @patch("modules.managers.delete_manager.app.validate_connection")
    @patch("modules.managers.delete_manager.app.validate_event_path_params")
    def test_lambda_handler_500_error(self, mock_validate_event_path_params, mock_validate_connection,
                                      mock_authorizate_user, mock_get_db_connection):
        # Configura los valores de retorno de los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')
        simulate_valid_validations(mock_validate_event_path_params, mock_validate_connection)

        self.mock_cursor.execute.side_effect = Exception("Simulated database error")

        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

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


if __name__ == '__main__':
    unittest.main()
