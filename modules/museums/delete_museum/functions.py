import json
import boto3
import psycopg2
from datetime import datetime, date


# Serializador de tipos de dato datetime
def datetime_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# Para funciones que consulten un array
def serialize_rows(rows, cursor):
    serialized_rows = []
    for row in rows:
        # Obtener nombres de columnas del cursor
        column_names = [desc[0] for desc in cursor.description]
        # Convertir la tupla a un diccionario
        serialized_row = dict(zip(column_names, row))
        # Agregar al array
        serialized_rows.append(serialized_row)
    return serialized_rows


# Para funciones que consulten un solo objeto
def serialize_row(row, cursor):
    if row is not None:
        # Obtener nombres de columnas del cursor
        column_names = [desc[0] for desc in cursor.description]
        # Convertir la tupla a un diccionario
        serialized_row = dict(zip(column_names, row))
        return serialized_row
    else:
        return None


def  get_db_connection():
    secrets = get_secrets()
    host = secrets['POSTGRES_HOST']
    user = 'default'
    password = secrets['POSTGRES_PASSWORD']
    database = secrets['POSTGRES_DATABASE']
    return psycopg2.connect(
       host= host,
       user= user,
       password= password,
       database= database
   )


def get_secrets():
 secret_name = "prod/musepa/vercel/postgres"
    region_name = "us-west-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except Exception as e:
        raise e

    secret = get_secret_value_response['SecretString']
    return json.loads(secret)