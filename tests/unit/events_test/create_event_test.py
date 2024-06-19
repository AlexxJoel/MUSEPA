import unittest
import json
from unittest.mock import patch, MagicMock
from modules.events.create_event.app import lambda_handler

# Simulación del cuerpo de la petición
mock_body = {
    "body": json.dumps({
        "name": "Nombre del evento",
        "description": "Descripcion del evento",
        "start_date": "2020-06-12",
        "end_date": "2020-06-12",
        "category": "Categoria del evento",
        "pictures": "URL de la imagen 1",
        "id_museum": "1"
    })
}


class MyTestCase(unittest.TestCase):

    @patch("modules.events.create_event.app.connect_database")
    def test_create_event_connect(
            self,
            mock_connect_database
    ):
        # Configuración de los mocks
        mock_connect_database.return_value = {'host': 'ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
                                              'user': 'default',
                                              'password': 'pnQI1h7sNfFK',
                                              'database': 'verceldb'}
        # Mock del cursor y la conexión
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect_database.return_value = mock_connection

    @patch("modules.events.create_event.app.connect_database")
    @patch("modules.events.create_event.app.close_connection")
    def test_create_event_success(
            self,
            mock_connect_database,
            mock_close_connection,
    ):
        # Configuración de los mocks
        mock_connect_database.return_value = {'host': 'ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
                                              'user': 'default',
                                              'password': 'pnQI1h7sNfFK',
                                              'database': 'verceldb'}
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect_database.return_value = mock_connection
        result = lambda_handler(mock_body, None)

        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Event created successfully"}))
        # Verifica que la conexión se haya cerrado al menos una vez con el argumento True
        mock_connect_database.return_value = True
        mock_close_connection.assert_any_call(True)


    @patch("modules.events.create_event.app.connect_database")
    @patch("modules.events.create_event.app.close_connection")
    def test_create_event_database_error(
            self,
            mock_connect_database,
            mock_close_connection
    ):
        # Configuración de los mocks
        mock_connect_database.return_value = {'host': 'ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech',
                                              'user': 'as',
                                              'password': 'asda',
                                              'database': 'verceldb'}

        # Mock del cursor y la conexión
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect_database.return_value = mock_connection

        # Simulación de un error en la base de datos
        mock_cursor.execute.side_effect = Exception("Database error")

        result = lambda_handler(mock_body, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("error", result["body"])
        mock_connect_database.return_value = True
        mock_close_connection.assert_any_call(True)


    @patch("modules.events.create_event.app.psycopg2.connect")
    @patch("modules.events.create_event.validations.validate_connection")
    def test_create_event_validation_error(
            self, mock_psycopg2_connect, mock_validate_connection
    ):
        # Configuración de los mocks
        mock_psycopg2_connect.return_value = MagicMock()
        mock_validate_connection.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid connection"}),
        }

        result = lambda_handler(mock_body, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("error", result["body"])
        mock_psycopg2_connect.assert_not_called()

    @patch("modules.events.create_event.app.psycopg2.connect")
    @patch("modules.events.create_event.validations.validate_connection")
    @patch("modules.events.create_event.validations.validate_event_body")
    def test_create_event_invalid_body(
            self, mock_psycopg2_connect, mock_validate_connection, mock_validate_event_body
    ):
        # Configuración de los mocks
        mock_psycopg2_connect.return_value = MagicMock()
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid event body"}),
        }

        result = lambda_handler(mock_body, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("error", result["body"])
        mock_psycopg2_connect.assert_not_called()

    @patch("modules.events.create_event.app.psycopg2.connect")
    @patch("modules.events.create_event.validations.validate_connection")
    @patch("modules.events.create_event.validations.validate_event_body")
    @patch("modules.events.create_event.validations.validate_payload")
    def test_create_event_invalid_payload(
            self,
            mock_psycopg2_connect,
            mock_validate_connection,
            mock_validate_event_body,
            mock_validate_payload,
    ):
        # Configuración de los mocks
        mock_psycopg2_connect.return_value = MagicMock()
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid payload"}),
        }

        result = lambda_handler(mock_body, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("error", result["body"])
        mock_psycopg2_connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
