import json
from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock
from modules.events.update_event.app import lambda_handler

class TestUpdateEvent(TestCase):

    @patch("modules.events.update_event.app.psycopg2.connect")
    @patch("modules.events.update_event.app.validate_connection")
    @patch("modules.events.update_event.app.validate_event_body")
    @patch("modules.events.update_event.app.validate_payload")
    def test_update_event_success(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection, mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        # Simular una respuesta exitosa de la consulta
        mock_cursor.fetchone.return_value = {'id': 1}

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {
            'body': json.dumps({
                'id': 1,
                'name': 'Event 1',
                'description': 'Description 1',
                'start_date': '2024-01-01T00:00:00Z',
                'end_date': '2024-01-02T00:00:00Z',
                'category': 'Category 1',
                'pictures': ['pic1', 'pic2'],
                'id_museum': 1
            })
        }
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Event updated successfully yeah!"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_connection.commit.assert_called_once()
        mock_connection.rollback.assert_not_called()

    @patch("modules.events.update_event.app.psycopg2.connect")
    @patch("modules.events.update_event.app.validate_connection")
    @patch("modules.events.update_event.app.validate_event_body")
    @patch("modules.events.update_event.app.validate_payload")
    def test_update_event_not_found(self, mock_validate_payload, mock_validate_event_body, mock_validate_connection, mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_body.return_value = None
        mock_validate_payload.return_value = None

        # Simular que no se encuentra el evento
        mock_cursor.fetchone.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {
            'body': json.dumps({
                'id': 999,
                'name': 'Event 1',
                'description': 'Description 1',
                'start_date': '2024-01-01T00:00:00Z',
                'end_date': '2024-01-02T00:00:00Z',
                'category': 'Category 1',
                'pictures': ['pic1', 'pic2'],
                'id_museum': 1
            })
        }
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 404)
        self.assertEqual(result["body"], json.dumps({"error": "Event not found"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_connection.commit.assert_not_called()
        mock_connection.rollback.assert_not_called()

if __name__ == "__main__":
    unittest.main()
