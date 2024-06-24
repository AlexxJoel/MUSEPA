import unittest
import json
from unittest.mock import patch, MagicMock
from modules.events.get_events.app import lambda_handler

class MyTestCase(unittest.TestCase):

    @patch("modules.events.create_event.app.psycopg2.connect")
    def test_lambda_handler_500_error(self,mock_psycopg2_connect):
        # Mock the connection and cursor
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simulate an exception when executing the SQL query
        mock_cursor.execute.side_effect = Exception("Simulated database error")

        # Call the lambda_handler function
        result = lambda_handler()
        print(result)
        # Verify the result
        self.assertEqual(result['statusCode'], 500)
        self.assertEqual(result["body"], json.dumps({"error": "Simulated database error"}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()

    @patch("modules.events.get_events.app.psycopg2.connect")
    def test_get_events_success(self, mock_psycopg2_connect):
        # Configurar el mock de la conexión de psycopg2
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_psycopg2_connect.return_value = mock_connection

        # Simular una respuesta exitosa de la consulta
        mock_cursor.fetchall.return_value = [{"id": 1, "name": "Event 1"}, {"id": 2, "name": "Event 2"}]

        # Ejecutar la función lambda_handler
        result = lambda_handler()

        # Imprimir el resultado (puede eliminarse en el código de producción)
        print(result)

        # Verificar el resultado esperado
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"],
                         json.dumps({"data": [{"id": 1, "name": "Event 1"}, {"id": 2, "name": "Event 2"}]}))

        # Verificar que se ha llamado a close_connection con el argumento correcto
        mock_connection.close.assert_called_once()
        mock_cursor.close.assert_called_once()

    

if __name__ == "__main__":
    unittest.main()
