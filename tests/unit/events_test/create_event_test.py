import json
from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock
from modules.events.create_event.app import lambda_handler

class TestCreateEvent(TestCase):

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

if __name__ == "__main__":
    unittest.main()
