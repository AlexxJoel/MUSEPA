import json

import boto3
from botocore.exceptions import ClientError
from psycopg2.extras import RealDictCursor

from authorization import authorizate_user
from connect_db import get_db_connection
from validations import validate_connection, validate_event_path_params


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Authorizate
        authorization_response = authorizate_user(event)
        if authorization_response is not None:
            return authorization_response

        # Database connection
        conn = get_db_connection()

        # Validate connection
        valid_conn_res = validate_connection(conn)
        if valid_conn_res is not None:
            return valid_conn_res

        # Validate path params in event
        valid_path_params_res = validate_event_path_params(event)
        if valid_path_params_res is not None:
            return valid_path_params_res

        # SonarQube/SonarCloud ignore end
        # Get values from path params
        request_id = event['pathParameters']['id']
        # SonarQube/SonarCloud ignore start
        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # Start transaction
        conn.autocommit = False

        # Find manager by id
        cur.execute("SELECT * FROM managers WHERE id = %s", (request_id,))
        manager = cur.fetchone()

        if not manager:
            return {"statusCode": 404, "body": json.dumps({"error": "Manager not found"})}

        cur.execute("SELECT * FROM users WHERE id = %s", (manager['id_user'],))
        user = cur.fetchone()

        # Delete manager
        cur.execute("DELETE FROM managers WHERE id = %s", (request_id,))

        # Delete related user
        cur.execute("DELETE FROM users WHERE id = %s", (manager['id_user'],))

        # Cognito Integration
        try:
            # Se colocan las credenciales que obtuvimos al generar lo de cognito
            # Configura el cliente de cognito
            client = boto3.client('cognito-idp', region_name='us-west-1')
            user_pool_id = "us-west-1_3onWfQPhK"

            # Eliminar el usuario actual
            client.admin_delete_user(
                UserPoolId=user_pool_id,
                Username=user["username"]
            )

            # Commit query
            conn.commit()

            # Si Cognito es exitoso, retorna la respuesta
            return {
                'statusCode': 200,
                'body': json.dumps({"message": "Manager deleted successfully"})
            }

        except ClientError as e:
            # Si Cognito falla, realiza rollback de la base de datos
            conn.rollback()
            return {
                'statusCode': 400,
                'body': json.dumps({"error": e.response['Error']['Message']})
            }

    except Exception as e:
        # Handle rollback
        if conn is not None:
            conn.rollback()
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    # SonarQube/SonarCloud ignore end
