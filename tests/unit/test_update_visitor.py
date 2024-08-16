import json
import unittest
from unittest import TestCase
from unittest.mock import patch, MagicMock
import boto3
from botocore.exceptions import ClientError
import jwt

from modules.visitors.update_visitor.app import lambda_handler
from modules.visitors.update_visitor.app import validate_connection, validate_event_body, validate_payload
from modules.visitors.update_visitor.app import get_db_connection,get_secrets
from modules.visitors.update_visitor.app import authorizate_user

def simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload):
    mock_validate_connection.return_value = None
    mock_validate_event_body.return_value = None
    mock_validate_payload.return_value = None

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

class TestUpdateVisitor(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.visitors.update_visitor.app.get_db_connection")
    @patch("modules.visitors.update_visitor.app.authorizate_user")
    @patch("modules.visitors.update_visitor.app.validate_connection")
    @patch("modules.visitors.update_visitor.app.validate_event_body")
    @patch("modules.visitors.update_visitor.app.validate_payload")
    @patch("modules.visitors.update_visitor.app.boto3.client")
    @patch("modules.visitors.update_visitor.app.get_secrets")
    def test_update_visitor_success(self, mock_get_secrets, mock_boto3_client, mock_validate_payload,
                                    mock_validate_event_body, mock_validate_connection, mock_authorizate_user,
                                    mock_get_db_connection):
        # Mocking the secrets
        mock_get_secrets.return_value = {
            'POSTGRES_HOST': 'mock_host',
            'POSTGRES_PASSWORD': 'mock_password',
            'POSTGRES_DATABASE': 'mock_database',
            'USER_POOL_ID': 'mock_user_pool_id'
        }

        # Simulate the database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_get_db_connection.return_value = mock_conn

        # Simulate the authorizate_user function returning None (indicating successful authorization)
        mock_authorizate_user.return_value = None

        # Simulate the validate_connection, validate_event_body, and validate_payload functions returning None
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        # Simulate finding the visitor by ID
        mock_cursor.fetchone.return_value = [10]  # Simulate a valid user ID

        # Simulate the Cognito client
        mock_cognito_client = MagicMock()
        mock_boto3_client.return_value = mock_cognito_client

        # Mock Cognito operations
        mock_cognito_client.admin_delete_user.return_value = {}
        mock_cognito_client.admin_create_user.return_value = {}
        mock_cognito_client.admin_set_user_password.return_value = {}
        mock_cognito_client.admin_add_user_to_group.return_value = {}

        # Create a test token
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Create a test event
        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'id': 3,
                'email': 'example@example.com',
                'username': 'test',
                'password': 'Test123.',
                'name': 'test',
                'surname': 'test',
                'lastname': 'test',
            })
        }

        # Execute the lambda_handler function
        result = lambda_handler(event, None)

        # Verify the expected result
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(json.loads(result["body"])["message"], "Visitor updated successfully")

        # Verify that the database commit was called
        mock_conn.commit.assert_called_once()

        # Verify that the Cognito client methods were called with expected arguments
        mock_cognito_client.admin_delete_user.assert_called_once_with(
            UserPoolId='mock_user_pool_id',
            Username='test'
        )

        mock_cognito_client.admin_create_user.assert_called_once_with(
            UserPoolId='mock_user_pool_id',
            Username='test',
            UserAttributes=[
                {'Name': 'email', 'Value': 'example@example.com'},
                {'Name': 'email_verified', 'Value': 'false'}
            ],
            TemporaryPassword='Test123.'
        )

        mock_cognito_client.admin_set_user_password.assert_called_once_with(
            UserPoolId='mock_user_pool_id',
            Username='test',
            Password='Test123.',
            Permanent=True
        )

        mock_cognito_client.admin_add_user_to_group.assert_called_once_with(
            UserPoolId='mock_user_pool_id',
            Username='test',
            GroupName="visitor"
        )

    @patch("modules.visitors.update_visitor.app.get_db_connection")
    @patch("modules.visitors.update_visitor.app.authorizate_user")
    def test_lambda_invalid_conn(self, mock_authorizate_user, mock_get_db_connection):
        # Simular la autorización y la conexión DB
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = None

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.visitors.update_visitor.app.get_db_connection")
    @patch("modules.visitors.update_visitor.app.authorizate_user")
    @patch("modules.visitors.update_visitor.app.validate_connection")
    def test_lamda_invalid_event_body(self, mock_validate_connection, mock_authorizate_user, mock_get_db_connection):
        # Simular la autorización y la conexión DB
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Crear un token de prueba
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

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.visitors.update_visitor.app.get_db_connection")
    @patch("modules.visitors.update_visitor.app.authorizate_user")
    @patch("modules.visitors.update_visitor.app.validate_connection")
    @patch("modules.visitors.update_visitor.app.validate_event_body")
    def test_create_invalid_payload(self, mock_validate_event_body, mock_validate_connection,
                                    mock_authorizate_user, mock_get_db_connection):
        # Simular la autorización y la conexión DB
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'id': 3,
                'email': 'examplexample.com',
                'username': 'test',
                'password': 'Test123.',
                'name': 'test',
                'surname': 'test',
                'lastname': 'test',
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

    @patch("modules.visitors.update_visitor.app.get_db_connection")
    @patch("modules.visitors.update_visitor.app.authorizate_user")
    @patch("modules.visitors.update_visitor.app.validate_connection")
    @patch("modules.visitors.update_visitor.app.validate_event_body")
    @patch("modules.visitors.update_visitor.app.validate_payload")
    def test_lambda_handler_500_error(self, mock_validate_payload, mock_validate_event_body,mock_validate_connection,
                                      mock_authorizate_user, mock_get_db_connection):
        # Simular la autorización y la conexión DB
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular una validación exitosa
        simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload)

        # Simular excepción
        self.mock_cursor.execute.side_effect = Exception("Simulated database error")

        # Simular request
        event = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'id': 3,
                'email': 'example@example.com',
                'username': 'test',
                'password': 'Test123.',
                'name': 'test',
                'surname': 'test',
                'lastname': 'test',
            })
        }
        result = lambda_handler(event, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Simulated database error"}))


class TestValidations(TestCase):
    def setUp(self):
        self.valid_payload = {
            'email': 'example@example.com',
            'username': 'test',
            'password': 'Test123.',
            'name': 'test',
            'surname': 'test',
            'lastname': 'test',
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
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'email'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_email(self):
        payload = self.valid_payload.copy()
        payload["email"] = "invalidemail"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'email'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_password(self):
        payload = self.valid_payload.copy()
        del payload["password"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'password'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_password(self):
        payload = self.valid_payload.copy()
        payload["password"] = None
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'password'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_username(self):
        payload = self.valid_payload.copy()
        del payload["username"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'username'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_username(self):
        payload = self.valid_payload.copy()
        payload["username"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'username'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_name(self):
        payload = self.valid_payload.copy()
        del payload["name"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_name(self):
        payload = self.valid_payload.copy()
        payload["name"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'name'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_surname(self):
        payload = self.valid_payload.copy()
        del payload["surname"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'surname'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_surname(self):
        payload = self.valid_payload.copy()
        payload["surname"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'surname'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_lastname(self):
        payload = self.valid_payload.copy()
        del payload["lastname"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'lastname'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_lastname(self):
        payload = self.valid_payload.copy()
        payload["lastname"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'lastname'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

class TestConnectDB(TestCase):
    @patch('modules.visitors.update_visitor.app.psycopg2.connect')
    @patch('modules.visitors.update_visitor.app.get_secrets')
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
