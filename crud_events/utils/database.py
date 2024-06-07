import logging
import psycopg2
import os

# Configuración de los registros
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Variables de entorno
user_name = os.environ.get('default')
password = os.environ.get('pnQI1h7sNfFK')
host = os.environ.get('ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech')
db_name = os.environ.get('verceldb')

# Función para obtener eventos desde la base de datos

def get_db_connection():
    try:
        # Crear la conexión a la base de datos
        conn = psycopg2.connect(
            host=host,
            user=user_name,
            password=password,
            database=db_name,
            connect_timeout=5
        )
    except psycopg2.Error as e:
        print(e)
        raise RuntimeError("ERROR EN CONEXION")