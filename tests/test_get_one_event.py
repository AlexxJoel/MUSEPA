import json
from unittest.mock import patch
import pytest
from crud_events.get_one_event import lambda_handler


# Fixture para el mock de la conexión a la base de datos
@pytest.fixture
def mock_conn():
    with patch('crud_events.utils.database.conn') as mock_conn:
        yield mock_conn


# Prueba para la función lambda_handler con éxito
def test_lambda_handler_success(mock_conn):
    # Mockear el cursor
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.execute.return_value = None

    event = {
        "body": json.dumps({
            "id_event": 1
        })
    }
    context = {}  # Puedes ajustar el contexto según sea necesario

    response = lambda_handler(event, context)
    body = json.loads(response['body'])
    print(response)


    assert response['statusCode'] == 200
    assert body['message'] == "Event get successfully."


# Prueba para la función lambda_handler con fallo
def test_lambda_handler_failure(mock_conn):
    # Mockear el cursor para lanzar una excepción
    mock_conn.cursor.side_effect = Exception("DB Connection Error")

    event = {
        "body": json.dumps({
            "id": 1,
        })
    }
    context = {}  # Puedes ajustar el contexto según sea necesario

    response = lambda_handler(event, context)
    print(response)

    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['message'] == "Error update events."

