import json
from unittest import TestCase
import unittest
from unittest.mock import patch,Mock
import boto3
from botocore.exceptions import ClientError

import jwt

from modules.works.update_work.app import lambda_handler
from modules.works.update_work.app import validate_connection, validate_event_body, validate_payload
from modules.works.update_work.app import get_db_connection,get_secrets
from modules.works.update_work.app import authorizate_user

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
        if SecretId == "prod/musepa/vercel/postgres":
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


class MockConnection:
    def __init__(self):
        self.cursor_instance = MockCursor()
        self.closed = False
        self.committed = False
        self.rolled_back = False


    def cursor(self):
        return self.cursor_instance

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def close(self):
        self.closed = True


class MockCursor:
    def __init__(self):
        self.closed = False
        self.executed_queries = []
        self.fetchone = Mock()

    def execute(self, query, params):
        self.executed_queries.append((query, params))

    def fetchone(self):
        # Retorna un valor predefinido
        return self.fetchone_result

    def close(self):
        self.closed = True



class TestUpdateEvent(TestCase):
    def setUp(self):
        self.mock_connection = MockConnection()
        self.mock_cursor = self.mock_connection.cursor_instance

    @patch("modules.works.update_work.app.get_db_connection")
    @patch("modules.works.update_work.app.authorizate_user")
    @patch("modules.works.update_work.app.validate_connection")
    @patch("modules.works.update_work.app.validate_event_body")
    @patch("modules.works.update_work.app.validate_payload")
    def test_update_event_success(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                                  mock_authorizate_user, mock_get_db_connection):
        # Configuramos los mocks
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Simular un resultado de fetchone válido
        self.mock_cursor.fetchone_result = (1,)  # O cualquier valor que necesites que retorne fetchone

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular validaciones exitosas
        simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload)

        # Simular el evento de actualización
        work = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'id': 1,
                'title': 'Title',
                'description': 'Description',
                'creation_date': '2024-01-01',
                'technique': 'puntos',
                'artists': 'more',
                'id_museum': 1,
                'pictures': ['pic1,pic2']
            })
        }

        # Ejecutar la función lambda_handler con el evento simulado
        result = lambda_handler(work, None)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Work updated successfully"}))

        # Verificar que se ha llamado a `close`, `commit` y que `rollback` no se ha llamado
        self.assertTrue(self.mock_connection.closed)
        self.assertTrue(self.mock_cursor.closed)
        self.assertTrue(self.mock_connection.committed)
        self.assertFalse(self.mock_connection.rolled_back)

    @patch("modules.works.update_work.app.get_db_connection")
    @patch("modules.works.update_work.app.authorizate_user")
    @patch("modules.works.update_work.app.validate_connection")
    @patch("modules.works.update_work.app.validate_event_body")
    @patch("modules.works.update_work.app.validate_payload")
    def test_update_event_not_found(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                                    mock_authorizate_user, mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')
        simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload)

        self.mock_cursor.fetchone = Mock(return_value=None)

        work = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'id': 2019,
                'title': 'Title',
                'description': 'Description',
                'creation_date': '2024-01-01',
                'technique': 'puntos',
                'artists': 'more',
                'id_museum': 1,
                'pictures': ['pic1,pic2']
            })
        }
        result = lambda_handler(work, None)
        print(result)

        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(result["body"], json.dumps({"error": "Work not found"}))

        # Verificar que se han cerrado la conexión y el cursor correctamente
        self.assertTrue(self.mock_connection.closed)
        self.assertTrue(self.mock_cursor.closed)



    @patch("modules.works.update_work.app.get_db_connection")
    @patch("modules.works.update_work.app.authorizate_user")
    def test_lambda_invalid_conn(self, mock_authorizate_user, mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = None

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        work = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'pathParameters': {'id': '1'}}
        result = lambda_handler(work, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.works.update_work.app.get_db_connection")
    @patch("modules.works.update_work.app.authorizate_user")
    @patch("modules.works.update_work.app.validate_connection")
    def test_lamda_invalid_event_body(self, mock_validate_connection, mock_authorizate_user, mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular una validación exitosa
        mock_validate_connection.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba sin cuerpo
        event = {'headers': {
            'Authorization': f'Bearer {token}'
        }}
        result = lambda_handler(event, None)

        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "No body provided."}))

        # Verificar que se ha cerrado la conexión correctamente
        self.assertTrue(self.mock_connection.closed)
        self.assertFalse(self.mock_cursor.closed)  # No se debería haber cerrado el cursor
        self.assertFalse(self.mock_connection.committed)
        self.assertFalse(self.mock_connection.rolled_back)

    @patch("modules.works.update_work.app.get_db_connection")
    @patch("modules.works.update_work.app.authorizate_user")
    @patch("modules.works.update_work.app.validate_connection")
    @patch("modules.works.update_work.app.validate_event_body")
    def test_create_invalid_payload(self, mock_validate_event_body, mock_validate_connection,
                                    mock_authorizate_user, mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None

        # Ejecutar la función lambda_handler con un payload inválido (falta 'title')
        work = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'id': 1,
                'description': 'Description',
                'creation_date': '2024-01-01',
                'technique': 'puntos',
                'artists': 'more',
                'id_museum': 1,
                'pictures': ['pic1,pic2']
            })
        }
        result = lambda_handler(work, None)

        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing 'title'"}))

        # Verificar que se ha cerrado la conexión correctamente
        self.assertTrue(self.mock_connection.closed)
        self.assertFalse(self.mock_cursor.closed)  # No se debería haber cerrado el cursor
        self.assertFalse(self.mock_connection.committed)
        self.assertFalse(self.mock_connection.rolled_back)

    @patch("modules.works.update_work.app.get_db_connection")
    @patch("modules.works.update_work.app.authorizate_user")
    @patch("modules.works.update_work.app.validate_connection")
    @patch("modules.works.update_work.app.validate_event_body")
    @patch("modules.works.update_work.app.validate_payload")
    def test_lambda_handler_500_error(self, mock_validate_payload, mock_validate_event_body,
                                      mock_validate_connection, mock_authorizate_user, mock_get_db_connection):
        mock_authorizate_user.return_value = None
        mock_get_db_connection.return_value = self.mock_connection

        # Crear un token de prueba
        token = jwt.encode({'cognito:groups': ['manager']}, 'secret', algorithm='HS256')

        # Simular una validación exitosa
        simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload)

        # Simular una excepción al ejecutar una consulta
        self.mock_cursor.execute = Mock(side_effect=Exception("Simulated database error"))

        work = {
            'headers': {
                'Authorization': f'Bearer {token}'
            },
            'body': json.dumps({
                'id': 1,
                'title': 'Title',
                'description': 'Description',
                'creation_date': '2024-01-01',
                'technique': 'puntos',
                'artists': 'more',
                'id_museum': 1,
                'pictures': ['pic1,pic2']
            })
        }
        result = lambda_handler(work, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Simulated database error"}))

        # Verificar que se ha cerrado la conexión y se ha llamado a rollback
        self.assertTrue(self.mock_connection.closed)
        self.assertTrue(self.mock_cursor.closed)
        self.assertFalse(self.mock_connection.committed)
        self.assertTrue(self.mock_connection.rolled_back)


class TestValidations(TestCase):
    def setUp(self):
        self.valid_payload = {
            'title': 'Title',
            'description': 'Description',
            'creation_date': '2024-01-01',
            'technique': 'puntos',
            'artists': ['more', 'pablo'],
            'id_museum': 1,
            'pictures': ['pic1', 'pic2']
        }

    @patch("modules.works.update_work.app.get_db_connection")
    def test_validate_connection_failure(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = None
        result = validate_connection(mock_psycopg2_connect.return_value)
        self.assertEqual(result["statusCode"], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    def test_validate_connection_success(self):
        conn = unittest.mock.MagicMock()
        result = validate_connection(conn)
        self.assertIsNone(result)

    def test_validate_event_body_success(self):
        work = {'body': json.dumps({"key": "value"})}
        result = validate_event_body(work)
        self.assertIsNone(result)

    def test_validate_event_body_no_body(self):
        work = {}
        result = validate_event_body(work)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "No body provided."}))

    def test_validate_event_body_null_body(self):
        work = {"body": None}
        result = validate_event_body(work)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body is null."}))

    def test_validate_event_body_empty_body(self):
        work = {"body": ""}
        result = validate_event_body(work)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body is empty."}))

    def test_validate_event_body_body_is_list(self):
        work = {"body": []}
        result = validate_event_body(work)
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Body can not be a list."}))

    def test_validate_event_body_invalid_json(self):
        work = {'body': "invalid json"}
        result = validate_event_body(work)
        self.assertEqual(result['statusCode'], 400)
        self.assertEqual(result["body"], json.dumps({"error": "The request body is not valid JSON"}))

    def test_validate_payload_valid(self):
        self.assertIsNone(validate_payload(self.valid_payload))

    def test_validate_payload_missing_name(self):
        payload = self.valid_payload.copy()
        del payload["title"]
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'title'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_name(self):
        payload = self.valid_payload.copy()
        payload["title"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'title'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_description(self):
        payload = self.valid_payload.copy()
        del payload['description']

        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'description'"}),'headers': headers}

        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_description(self):
        payload = self.valid_payload.copy()
        payload["description"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'description'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_start_date(self):
        payload = self.valid_payload.copy()
        del payload['creation_date']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'creation_date'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_start_date(self):
        payload = self.valid_payload.copy()
        payload["creation_date"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'creation_date'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_category(self):
        payload = self.valid_payload.copy()
        del payload['technique']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'technique'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_category(self):
        payload = self.valid_payload.copy()
        payload["technique"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'technique'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_category(self):
        payload = self.valid_payload.copy()
        del payload['artists']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'artists'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_category(self):
        payload = self.valid_payload.copy()
        payload["artists"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'artists'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_id_museum(self):
        payload = self.valid_payload.copy()
        del payload['id_museum']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id_museum'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_id_museum(self):
        payload = self.valid_payload.copy()
        payload["id_museum"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'id_museum'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_pictures(self):
        payload = self.valid_payload.copy()
        del payload['pictures']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"}),'headers': headers}
        self.assertEqual(validate_payload(payload), expected_response)

class TestConnectDB(TestCase):
    @patch('modules.works.update_work.app.psycopg2.connect')
    @patch('modules.works.update_work.app.get_secrets')
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

    def test_authorization_visitor_role(self):
        # Simula un evento con un token válido pero con el rol 'visitor'
        token_payload = {
            "cognito:groups": ["visitor"]
        }
        token = jwt.encode(token_payload, key="secret", algorithm="HS256")
        event = {
            "headers": {
                "Authorization": f"Bearer {token}"
            }
        }

        result = authorizate_user(event)
        expected_result = {
            'statusCode': 403,
            'body': json.dumps({"error": "Access denied: insufficient permissions"}),
            'headers': headers
        }
        self.assertEqual(result, expected_result)

    def test_authorization_no_token(self):
        # Simula un evento sin token en los headers
        event = {
            "headers": {
                "Authorization": ""
            }
        }

        with self.assertRaises(IndexError):
            authorizate_user(event)



if __name__ == "__main__":
    unittest.main()
