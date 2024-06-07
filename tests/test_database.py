import unittest
import psycopg2
import os
from unittest.mock import patch, MagicMock

from crud_events.utils.database import get_db_connection  # Reemplaza 'tu_modulo' con el nombre real del archivo


class TestGetDbConnection(unittest.TestCase):

    @patch('psycopg2.connect')
    def test_get_db_connection_success(self, mock_connect):
        # Configurar las variables de entorno (mock)
        db_user = os.environ['DB_USER']
        db_pswd = os.environ['DB_PSWD']
        db_host = os.environ['DB_HOST']
        db_name = os.environ['DB_NAME']

        # Simular una conexión exitosa
        mock_connect.return_value = MagicMock()  # Simula un objeto de conexión

        # Llamar a la función get_db_connection()
        conn = get_db_connection()

        # Verificar que la conexión se haya realizado correctamente
        mock_connect.assert_called_once_with(
            host=db_host,
            user=db_user,
            password=db_pswd,
            database=db_name,
            connect_timeout=5
        )
        self.assertIsNotNone(conn)  # Verificar que se devuelve un objeto de conexión

    @patch('psycopg2.connect')
    def test_get_db_connection_error(self, mock_connect):
        # Simular un error en la conexión
        mock_connect.side_effect = psycopg2.Error('Error de conexión simulada')

        # Verificar que se lance la excepción correcta
        with self.assertRaises(psycopg2.Error):
            get_db_connection()

        # Verificar que se haya llamado a mock_connect una vez
        mock_connect.assert_called_once()