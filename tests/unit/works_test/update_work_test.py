import json
from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock
from modules.works.update_work.app import lambda_handler
from modules.works.update_work.validations import validate_connection, validate_event_body, validate_payload


def simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload):
    mock_validate_connection.return_value = None
    mock_validate_event_body.return_value = None
    mock_validate_payload.return_value = None


class TestUpdateEvent(TestCase):
    def setUp(self):
        self.mock_connection = MagicMock()
        self.mock_cursor = MagicMock()
        self.mock_connection.cursor.return_value = self.mock_cursor

    @patch("modules.works.update_work.app.psycopg2.connect")
    @patch("modules.works.update_work.app.validate_connection")
    @patch("modules.works.update_work.app.validate_event_body")
    @patch("modules.works.update_work.app.validate_payload")
    def test_update_event_success(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                                  mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload)

        work = {
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
        print(result)

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Work updated successfully"}))

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()
        self.mock_connection.commit.assert_called_once()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.works.update_work.app.psycopg2.connect")
    @patch("modules.works.update_work.app.validate_connection")
    @patch("modules.works.update_work.app.validate_event_body")
    @patch("modules.works.update_work.app.validate_payload")
    def test_update_event_not_found(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection,
                                    mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = self.mock_connection
        simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload)

        self.mock_cursor.fetchone.return_value = None

        work = {
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

        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_called_once()

    @patch("modules.works.update_work.app.psycopg2.connect")
    def test_lambda_invalid_conn(self, mock_psycopg2_connect):
        mock_psycopg2_connect.return_value = None

        work = {'pathParameters': {'id': '1'}}
        result = lambda_handler(work, None)

        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Connection to the database failed"}))

    @patch("modules.works.update_work.app.psycopg2.connect")
    @patch("modules.works.update_work.app.validate_connection")
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

    @patch("modules.works.update_work.app.psycopg2.connect")
    @patch("modules.works.update_work.app.validate_connection")
    @patch("modules.works.update_work.app.validate_event_body")
    def test_create_invalid_payload(self, mock_validate_event_body, mock_validate_connection,
                                    mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        work = {
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

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 400)
        self.assertEqual(result["body"], json.dumps({"error": "Invalid or missing 'title'"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        self.mock_connection.close.assert_called_once()
        self.mock_cursor.close.assert_not_called()
        self.mock_connection.commit.assert_not_called()
        self.mock_connection.rollback.assert_not_called()

    @patch("modules.works.update_work.app.psycopg2.connect")
    @patch("modules.works.update_work.app.validate_connection")
    @patch("modules.works.update_work.app.validate_event_body")
    @patch("modules.works.update_work.app.validate_payload")
    def test_lambda_handler_500_error(self, mock_validate_payload, mock_validate_event_body,
                                      mock_validate_connection, mock_psycopg2_connect):
        # Simular conexión
        mock_psycopg2_connect.return_value = self.mock_connection

        # Simular una validación exitosa
        simulate_valid_validations(mock_validate_connection, mock_validate_event_body, mock_validate_payload)

        # Simular excepción
        self.mock_cursor.execute.side_effect = Exception("Simulated database error")

        work = {
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


class TestValidations(TestCase):
    def setUp(self):
        self.valid_payload = {
            'title': 'Titleeee',
            'description': 'Descriptiooon',
            'creation_date': '2024-01-01',
            'technique': 'puntooos',
            'artists': 'morrre',
            'id_museum': '1',
            'pictures': 'pic1,pic2'
        }

    @patch("modules.works.update_work.app.psycopg2.connect")
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
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'title'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_name(self):
        payload = self.valid_payload.copy()
        payload["title"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'title'"})}
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
        del payload['creation_date']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'creation_date'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_start_date(self):
        payload = self.valid_payload.copy()
        payload["creation_date"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'creation_date'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_category(self):
        payload = self.valid_payload.copy()
        del payload['technique']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'technique'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_category(self):
        payload = self.valid_payload.copy()
        payload["technique"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'technique'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_missing_category(self):
        payload = self.valid_payload.copy()
        del payload['artists']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'artists'"})}
        self.assertEqual(validate_payload(payload), expected_response)

    def test_validate_payload_invalid_category(self):
        payload = self.valid_payload.copy()
        payload["artists"] = "Invalid123!"
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'artists'"})}
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

    def test_validate_payload_missing_pictures(self):
        payload = self.valid_payload.copy()
        del payload['pictures']
        expected_response = {"statusCode": 400, "body": json.dumps({"error": "Invalid or missing 'pictures'"})}
        self.assertEqual(validate_payload(payload), expected_response)


if __name__ == "__main__":
    unittest.main()
