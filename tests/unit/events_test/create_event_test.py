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

# Simulación del provocación de fallas
mock_body_payload = {
    "body": json.dumps({
        "name": "Nombre del evento",
        "description": "Descripcion del evento",
        "start_date": "AAA-06-12",
        "end_date": "2020-06-12",
        "category": "Categoria del evento",
        "pictures": "URL de la imagen 1",
        "id_museum": "1"
    })
}


class MyTestCase(unittest.TestCase):

    @patch("modules.events.create_event.app.connect_database")
    def test_create_event_connect(self,mock_connect_database):
        mock_connect_database.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect_database.return_value = mock_connection

    @patch("modules.events.create_event.app.connect_database")
    @patch("modules.events.create_event.app.close_connection")
    def test_create_event_success(self,mock_connect_database,mock_close_connection):
        mock_connect_database.return_value = True
        mock_connection = MagicMock()
        mock_cursor = MagicMock()
        mock_connection.cursor.return_value = mock_cursor
        mock_connect_database.return_value = mock_connection
        result = lambda_handler(mock_body, None)
        print(result)
        self.assertEqual(result["statusCode"], 200)
        self.assertEqual(result["body"], json.dumps({"message": "Event created successfully"}))
        mock_close_connection.assert_any_call(True)

    @patch("modules.events.create_event.app.connect_database")
    @patch("modules.events.create_event.app.close_connection")
    @patch("modules.events.create_event.validations.validate_event_body")
    def test_create_event_invalid_body(
            self,
            mock_connect_database,
            mock_close_connection,
            mock_validate_event_body,
    ):
        # Simular la conexión a la base de datos
        mock_connect_database.return_value = True

        # Simular la validación del cuerpo del evento
        mock_validate_event_body.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Body can not be a list."}),
        }

        # Ejemplo de cuerpo de prueba que es una lista
        mock_body_test = {"body": []}

        # Ejecutar el handler de lambda con el cuerpo de prueba
        result = lambda_handler(mock_body_test, None)

        # Imprimir los resultados (puede eliminarse en el código de producción)
        print(result)

        # Verificar que el status code sea 400
        self.assertEqual(result["statusCode"], 400)

        # Verificar que el cuerpo contenga el mensaje de error correcto
        result_body = json.loads(result["body"])
        self.assertIn("error", result_body)
        self.assertEqual(result_body["error"], "Body is empty.")

    @patch("modules.events.create_event.app.connect_database")
    @patch("modules.events.create_event.app.close_connection")
    @patch("modules.events.create_event.validations.validate_payload")
    def test_create_event_invalid_payload(
            self,
            mock_connect_database,
            mock_close_connection,
            mock_validate_payload,
    ):
        mock_connect_database.return_value = True
        mock_validate_payload.return_value = {
            "statusCode": 400,
            "body": json.dumps({"error": "Invalid or missing"}),
        }

        result = lambda_handler(mock_body_payload, None)

        print(result)
        self.assertEqual(result["statusCode"], 400)
        result_body = json.loads(result["body"])
        self.assertIn("error", result_body)
        self.assertEqual(result_body["error"], "Invalid or missing")


if __name__ == "__main__":
    unittest.main()
