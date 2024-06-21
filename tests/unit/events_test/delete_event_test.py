import json
from unittest import TestCase
import unittest
from unittest.mock import patch, MagicMock
from modules.events.delete_event.app import lambda_handler

class TestDeleteEvent(TestCase):

    @patch("modules.events.delete_event.app.psycopg2.connect")
    @patch("modules.events.delete_event.app.validate_connection")
    @patch("modules.events.delete_event.app.validate_event_path_params")
    def test_delete_event_success(self, mock_validate_event_path_params, mock_validate_connection, mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_path_params.return_value = None

        # Simular una respuesta exitosa de la consulta
        mock_cursor.fetchone.return_value = {'id': 1}

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {'pathParameters': {'id': '1'}}
        result = lambda_handler(event, None)

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Event deleted successfully"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()
        mock_connection.commit.assert_called_once()
        mock_connection.rollback.assert_not_called()

    @patch("modules.events.delete_event.app.psycopg2.connect")
    @patch("modules.events.delete_event.app.validate_connection")
    @patch("modules.events.delete_event.app.validate_event_path_params")
    def test_delete_event_not_found(self, mock_validate_event_path_params, mock_validate_connection, mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simular una validación exitosa
        mock_validate_connection.return_value = None
        mock_validate_event_path_params.return_value = None

        # Simular que no se encuentra el evento
        mock_cursor.fetchone.return_value = None

        # Ejecutar la función lambda_handler con un evento de prueba
        event = {'pathParameters': {'id': '999'}}
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
