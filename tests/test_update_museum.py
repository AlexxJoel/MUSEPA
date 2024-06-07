import json
from unittest.mock import patch

import pytest

from crud_museums.update_museum import lambda_handler


# Fixture para el mock de la conexión a la base de datos
@pytest.fixture
def mock_conn():
    with patch('crud_museums.utils.database.conn') as mock_conn:
        yield mock_conn


# Prueba para la función lambda_handler con éxito
def test_lambda_handler_success(mock_conn):
    # Mockear el cursor
    mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
    mock_cursor.execute.return_value = None

    museum = {
        "body": json.dumps({
            "id": 2,
            "name": "Updated museum",
            "location": None,
            "tariffs": None,
            "schedules": None,
            "contact_number": None,
            "contact_email": None,
            "id_owner": None,
            "pictures": None
        })
    }
    context = {}  # Puedes ajustar el contexto según sea necesario

    response = lambda_handler(museum, context)
    print(response)

    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == "Museum updated successfully."


# Prueba para la función lambda_handler con fallo
def test_lambda_handler_failure(mock_conn):
    # Mockear el cursor para lanzar una excepción
    mock_conn.cursor.side_effect = Exception("DB Connection Error")

    museum = {
        "body": json.dumps({
            "id": 2,
            "name": "Updated museum",
            "location": None,
            "tariffs": None,
            "schedules": None,
            "contact_number": None,
            "contact_email": None,
            "id_owner": None,
            "pictures": None
        })
    }
    context = {}  # Puedes ajustar el contexto según sea necesario

    response = lambda_handler(museum, context)
    print(response)

    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert body['message'] == "Error update events."

#
# # Prueba para la función update_event con éxito
# def test_update_event_success(mock_conn):
#     # Mockear el cursor
#     mock_cursor = mock_conn.cursor.return_value.__enter__.return_value
#     mock_cursor.execute.return_value = None
#
#     event = {
#         "id": 1,
#         "name": "Updated Event",
#         "description": "Updated Description",
#         "start_date": "2024-06-06",
#         "end_date": "2024-06-07",
#         "event": "Updated Category",
#         "pictures": "updated_picture_url"
#     }
#
#     response = update_event(event)
#
#     assert response == "Update event successfully."
#     mock_cursor.execute.assert_called_once_with(
#         """UPDATE events SET name=%s,description=%s,start_date=%s,end_date=%s,category=%s,pictures=%s WHERE id =%s""",
#         ("Updated Event", "Updated Description", "2024-06-06", "2024-06-07", "Updated Category", "updated_picture_url",
#          1)
#     )
#
#
# # Prueba para la función update_event con fallo
# def test_update_event_failure(mock_conn):
#     # Mockear el cursor para lanzar una excepción
#     mock_conn.cursor.side_effect = psycopg2.Error("DB Error")
#
#     event = {
#         "id": 1,
#         "name": "Updated Event",
#         "description": "Updated Description",
#         "start_date": "2024-06-06",
#         "end_date": "2024-06-07",
#         "event": "Updated Category",
#         "pictures": "updated_picture_url"
#     }
#
#     with pytest.raises(RuntimeError) as excinfo:
#         update_event(event)
#
#     assert str(excinfo.value) == "ERROR EN ACTUALIZAR"