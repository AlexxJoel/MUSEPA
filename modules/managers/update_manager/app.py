import json

import boto3
from botocore.exceptions import ClientError

from authorization import authorizate_user
from connect_db import get_db_connection
from validations import validate_connection, validate_event_body, validate_payload


def lambda_handler(event, _context):
    conn = None
    cur = None
    try:
       
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

        # Validate body in event
        valid_event_body_res = validate_event_body(event)
        if valid_event_body_res is not None:
            return valid_event_body_res

        # Validate payload
        request_body = json.loads(event['body'])
        valid_payload_res = validate_payload(request_body)
        if valid_payload_res is not None:
            return valid_payload_res

        
        # Get payload values
        id = request_body['id']
        email = request_body['email']
        password = request_body['password']
        username = request_body['username']
        name = request_body['name']
        surname = request_body['surname']
        lastname = request_body['lastname']
        phone_number = request_body['phone_number']
        address = request_body['address']
        birthdate = request_body['birthdate']
        id_museum = request_body['id_museum']
       
        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Find manager by id_user
        cur.execute("SELECT id_user FROM managers WHERE id = %s", (id,))
        result = cur.fetchone()

        if not result:
            return {"statusCode": 404, "body": json.dumps({"error": "Manager not found"})}

        user_id = result[0]

        # Update user by user_id
        update_user_query = """UPDATE users SET email = %s, password = %s, username = %s WHERE id = %s """
        cur.execute(update_user_query, (email, password, username, user_id))

        # Update manager by manager_id
        update_manager_query = """ UPDATE managers SET name = %s, surname = %s, lastname = %s, phone_number = %s, address = %s, birthdate = %s, id_museum = %s  WHERE id = %s """
        cur.execute(update_manager_query, (name, surname, lastname, phone_number, address, birthdate, id_museum, id))

        # Cognito Integration
        try:
            # Se colocan las credenciales que obtuvimos al generar lo de cognito
            # Configura el cliente de cognito
            client = boto3.client('cognito-idp', region_name='us-west-1')
            user_pool_id = "us-west-1_3onWfQPhK"

            # Eliminar el usuario actual
            client.admin_delete_user(
                UserPoolId=user_pool_id,
                Username=username
            )

            # Crear un nuevo usuario con el nuevo username
            client.admin_create_user(
                UserPoolId=user_pool_id,
                Username=username,
                UserAttributes=[
                    {'Name': 'email', 'Value': email},
                    {"Name": 'email_verified', 'Value': 'false'}
                ],
                TemporaryPassword=password
            )

            # Marcar la contraseña temporal como cambiada en Cognito
            client.admin_set_user_password(
                UserPoolId=user_pool_id,
                Username=username,
                Password=password,
                Permanent=True
            )

            client.admin_add_user_to_group(
                UserPoolId=user_pool_id,
                Username=username,
                GroupName="manager"
            )

            # Commit query
            conn.commit()

            # Si Cognito es exitoso, retorna la respuesta
            return {
                'statusCode': 200,
                'body': json.dumps({"message": "Manager updated successfully."})
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
    
