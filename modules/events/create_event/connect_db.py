import psycopg2
import json
def connect_database(host,user, password, database):
    try:
        conn = psycopg2.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        return conn
    except Exception as e:
        # Handle rollback
        if conn is not None:
            conn.rollback()
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}


def close_connection(connection):
    if connection:
        connection.close()