import sys
import logging
import psycopg2
import os

# Configuración de los registros
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Variables de entorno
os.environ['DB_USER'] = 'default'
os.environ['DB_PSWD'] = 'pnQI1h7sNfFK'
os.environ['DB_HOST'] = 'ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech'
os.environ['DB_NAME'] = 'verceldb'

# Obtener valores de las variables de entorno
db_user = os.environ['DB_USER']
db_pswd = os.environ['DB_PSWD']
db_host = os.environ['DB_HOST']
db_name = os.environ['DB_NAME']

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def get_db_connection():
    try:
        # Crear la conexión a la base de datos
        return psycopg2.connect(
            host=db_host,
            user=db_user,
            password=db_pswd,
            database=db_name,
            connect_timeout=5
        )
    except psycopg2.Error as e:
        print(e)
        raise RuntimeError("ERROR EN CONEXION")


conn = get_db_connection()