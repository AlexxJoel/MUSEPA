import json

from unittest import TestCase
import unittest
from unittest.mock import MagicMock, patch
import boto3
from botocore.exceptions import ClientError
import jwt
from modules.museums.update_museum.app import lambda_handler,validate_connection,get_db_connection,get_secrets,validate_payload,validate_event_body,authorizate_user

headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'PUT'
}
class FakeConnection:
    """Clase que simula una conexión de psycopg2"""
    def close(self):
        pass

class FakeSecretsManagerClient:
    """Simula el cliente de Secrets Manager de boto3."""
    def get_secret_value(self, SecretId):
        if SecretId == "prod/musepa":
            return {
                'SecretString': json.dumps({
                    'POSTGRES_HOST': 'localhost',
                    'POSTGRES_PASSWORD': 'fake_password',
                    'POSTGRES_DATABASE': 'fake_database'
                })
            }
        else:
            raise ClientError(
                {"Error": {"Code": "ResourceNotFoundException"}},
                "get_secret_value"
            )

class FakeSession:
    """Simula una sesión de boto3."""
    def client(self, service_name, region_name):
        if service_name == 'secretsmanager' and region_name == 'us-west-1':
            return FakeSecretsManagerClient()
        else:
            raise ValueError("Unsupported service or region")


class TestMuseumUpdateLambda(unittest.TestCase):

    @patch('modules.museums.update_museum.app.authorizate_user')
    @patch('modules.museums.update_museum.app.get_db_connection')
    @patch('modules.museums.update_museum.app.validate_connection')
    @patch('modules.museums.update_museum.app.validate_event_body')
    @patch('modules.museums.update_museum.app.validate_payload')
    def test_lambda_handler_success(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                                    mock_get_db_connection, mock_authorizate_user):
        # Mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = MagicMock()
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = (1,)
        mock_conn = mock_get_db_connection.return_value
        mock_conn.cursor.return_value = mock_cursor

        event = {
            'headers': {'Authorization': 'Bearer valid_token'},
            'body': json.dumps({
                'id': 1,
                'name': 'Museum Name',
                'location': 'Location',
                'tariffs': '10.00',
                'schedules': '9am-5pm',
                'contact_number': '+1234567890',
                'contact_email': 'email@example.com',
                'pictures': 'url'
            })
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 200)
        self.assertIn('Museum updated successfully', response['body'])

    @patch('modules.museums.update_museum.app.authorizate_user')
    @patch('modules.museums.update_museum.app.get_db_connection')
    @patch('modules.museums.update_museum.app.validate_connection')
    @patch('modules.museums.update_museum.app.validate_event_body')
    @patch('modules.museums.update_museum.app.validate_payload')
    def test_lambda_handler_museum_not_found(self, mock_validate_payload, mock_validate_event_body,
                                             mock_validate_connection, mock_get_db_connection, mock_authorizate_user):
        # Mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = MagicMock()
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None
        mock_conn = mock_get_db_connection.return_value
        mock_conn.cursor.return_value = mock_cursor

        event = {
            'headers': {'Authorization': 'Bearer valid_token'},
            'body': json.dumps({
                'id': 999,
                'name': 'Museum Name',
                'location': 'Location',
                'tariffs': '10.00',
                'schedules': '9am-5pm',
                'contact_number': '+1234567890',
                'contact_email': 'email@example.com',
                'pictures': 'url'
            })
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Museum not found', response['body'])

    @patch('modules.museums.update_museum.app.authorizate_user')
    @patch('modules.museums.update_museum.app.get_db_connection')
    @patch('modules.museums.update_museum.app.validate_connection')
    @patch('modules.museums.update_museum.app.validate_event_body')
    @patch('modules.museums.update_museum.app.validate_payload')
    def test_lambda_handler_authorization_failure(self, mock_validate_payload, mock_validate_event_body,
                                                  mock_validate_connection, mock_get_db_connection,
                                                  mock_authorizate_user):
        # Mocks
        mock_authorizate_user.return_value = {'statusCode': 403,
                                              'body': json.dumps({"error": "Access denied: insufficient permissions"}),
                                              'headers': {}}

        event = {
            'headers': {'Authorization': 'Bearer invalid_token'},
            'body': json.dumps({})
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 403)
        self.assertIn('Access denied: insufficient permissions', response['body'])

    @patch('modules.museums.update_museum.app.authorizate_user')
    @patch('modules.museums.update_museum.app.get_db_connection')
    def test_lambda_handler_db_connection_failure(self, mock_get_db_connection, mock_authorizate_user):
        # Mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = None

        event = {
            'headers': {'Authorization': 'Bearer valid_token'},
            'body': json.dumps({})
        }

        response = lambda_handler(event, None)

        self.assertEqual(response['statusCode'], 500)
        self.assertIn('Connection to the database failed', response['body'])



class TestValidations(TestCase):
    def setUp(self):
        self.valid_payload = {
            'name': 'Event Name',
            'location': 'Event Location',
            'tariffs': '100',
            'schedules': 'Event Schedules',
            'contact_number': '123-456-7890',
            'contact_email': 'contact@example.com',
            'pictures': ['pic1']
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
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_name(self):
        payload = self.valid_payload.copy()
        payload['name'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)



    def test_validate_payload_missing_location(self):
        payload = self.valid_payload.copy()
        del payload['location']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'location'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_location(self):
        payload = self.valid_payload.copy()
        payload['location'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'location'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_tariffs(self):
        payload = self.valid_payload.copy()
        del payload['tariffs']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'tariffs'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_tariffs(self):
        payload = self.valid_payload.copy()
        payload['tariffs'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'tariffs'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_schedules(self):
        payload = self.valid_payload.copy()
        del payload['schedules']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'schedules'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_schedules(self):
        payload = self.valid_payload.copy()
        payload['schedules'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'schedules'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_contact_number(self):
        payload = self.valid_payload.copy()
        del payload['contact_number']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_number'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)


    def test_validate_payload_missing_contact_email(self):
        payload = self.valid_payload.copy()
        del payload['contact_email']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_email'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)


    def test_validate_payload_invalid_contact_email(self):
        payload = self.valid_payload.copy()
        payload['contact_email'] = 'invalidcontactemail'
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'contact_email'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_pictures(self):
        payload = self.valid_payload.copy()
        del payload['pictures']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_pictures(self):
        payload = self.valid_payload.copy()
        payload['pictures'] = 123
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)



class TestConnectDB(TestCase):
    @patch('modules.museums.update_museum.app.psycopg2.connect')
    @patch('modules.museums.update_museum.app.get_secrets')
    def test_get_db_connection(self, mock_get_secrets, mock_psycopg2_connect):
        # Simula la respuesta de get_secrets
        mock_get_secrets.return_value = {
            'POSTGRES_HOST': 'localhost',
            'POSTGRES_PASSWORD': 'fake_password',
            'POSTGRES_DATABASE': 'fake_database'
        }

        # Crea una instancia de la conexión simulada
        fake_connection = FakeConnection()
        mock_psycopg2_connect.return_value = fake_connection

        # Llama a la función que se está probando
        conn = get_db_connection()

        # Verifica que get_secrets fue llamada una vez
        mock_get_secrets.assert_called_once()

        # Verifica que psycopg2.connect fue llamada con los parámetros correctos
        mock_psycopg2_connect.assert_called_once_with(
            host='localhost',
            user='default',
            password='fake_password',
            database='fake_database'
        )

        # Verifica que la conexión devuelta es la misma que la simulada
        self.assertEqual(conn, fake_connection)

    def test_get_secrets_success(self):
        # Parcha la sesión de boto3 con una sesión simulada
        original_session = boto3.session.Session
        try:
            boto3.session.Session = FakeSession
            secrets = get_secrets()
            expected_secrets = {
                'POSTGRES_HOST': 'localhost',
                'POSTGRES_PASSWORD': 'fake_password',
                'POSTGRES_DATABASE': 'fake_database'
            }
            self.assertEqual(secrets, expected_secrets)
        finally:
            # Restaura la sesión original
            boto3.session.Session = original_session

    def test_get_secrets_failure(self):
        # Parcha la sesión de boto3 con una sesión simulada que falla
        original_session = boto3.session.Session
        try:
            class FailingSecretsManagerClient:
                def get_secret_value(self, SecretId):
                    raise ClientError(
                        {"Error": {"Code": "ResourceNotFoundException"}},
                        "get_secret_value"
                    )

            class FailingSession:
                def client(self, service_name, region_name):
                    return FailingSecretsManagerClient()

            boto3.session.Session = FailingSession

            with self.assertRaises(ClientError):
                get_secrets()
        finally:
            # Restaura la sesión original
            boto3.session.Session = original_session


class TestAuthorization(TestCase):
    def test_authorization_success(self):
        # Simula un evento con un token válido y un rol permitido
        token_payload = {
            "cognito:groups": ["admin"]
        }
        token = jwt.encode(token_payload, key="secret", algorithm="HS256")
        event = {
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        }

        result = authorizate_user(event)
        self.assertIsNone(result)



    def test_authorization_no_token(self):
        # Simula un evento sin token en los headers
        event = {
            "headers": {
                "Authorization": ""
            }
        }

        with self.assertRaises(IndexError):
            authorizate_user(event)




if __name__ == '__main__':
    unittest.main()
