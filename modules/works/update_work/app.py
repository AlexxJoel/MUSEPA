import json

from connect_db import get_db_connection
from validations import validate_connection, validate_event_body, validate_payload
from authorization import authorizate_user


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

        # Validate body in event
        valid_event_body_res = validate_event_body(event)
        if valid_event_body_res is not None:
            return valid_event_body_res

        # Validate payload
        request_body = json.loads(event['body'])
        valid_payload_res = validate_payload(request_body)
        if valid_payload_res is not None:
            return valid_payload_res

        # SonarQube/SonarCloud ignore end
        # Get payload values
        id = request_body['id']
        title = request_body['title']
        description = request_body['description']
        creation_date = request_body['creation_date']
        technique = request_body['technique']
        artists = request_body['artists']
        id_museum = request_body['id_museum']
        pictures = request_body['pictures']
        # SonarQube/SonarCloud ignore start
        # Create cursor
        cur = conn.cursor()

        # Start transaction
        conn.autocommit = False

        # Find work by id
        cur.execute("SELECT * FROM works WHERE id = %s", (id,))
        work = cur.fetchone()

        if not work:
            return {"statusCode": 404, "body": json.dumps({"error": "Work not found"})}

        # Update work by id
        sql = """UPDATE works SET title=%s, description=%s, creation_date=%s, technique=%s, artists=%s, id_museum=%s, pictures=%s WHERE id=%s"""
        cur.execute(sql, (title, description, creation_date, technique, artists, id_museum, pictures, id))

        # Commit query
        conn.commit()
        return {'statusCode': 200, 'body': json.dumps({"message": "Work updated successfully"})}
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
