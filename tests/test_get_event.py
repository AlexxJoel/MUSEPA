import json
import pytest
from unittest.mock import patch, MagicMock
from crud_events.get_event import lambda_handler, get_events

# Mocks
@pytest.fixture
def mock_conn():
    with patch('crud_events.utils.database.conn') as mock_conn:
        yield mock_conn

@pytest.fixture
def mock_cursor():
    cursor = MagicMock()
    cursor.fetchall.return_value = [{"id": 1, "name": "Test Event"}]
    return cursor

def test_lambda_handler_success(mock_conn, mock_cursor):
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

    event = {}  # Puedes ajustar el evento según sea necesario
    context = {}  # Puedes ajustar el contexto según sea necesario

    response = lambda_handler(event, context)
    body = json.loads(response['body'])
    print(response)

    assert response['statusCode'] == 200
    assert body['message'] == "Events retrieved successfully."

def test_lambda_handler_failure(mock_conn):
    mock_conn.cursor.side_effect = Exception("DB Connection Error")

    event = {}  # Puedes ajustar el evento según sea necesario
    context = {}  # Puedes ajustar el contexto según sea necesario

    response = lambda_handler(event, context)

    assert response['statusCode'] == 500
    # body = json.loads(response['body'])
    # assert body['message'] == "Error retrieving events."