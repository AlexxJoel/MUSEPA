import json
import jwt

headers = {
    'Access-Control-Allow-Headers': '*',
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET'
}

def authorizate_user(_event):
    token = _event['headers']['Authorization'].split(' ')[1]
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    roles = decoded_token.get('cognito:groups')
    role = roles[0]

    if role is None:
        return {'statusCode': 400, 'body': json.dumps({"error": "Role not found in token"}), "headers": headers}

    if len(roles) <= 0:
        return {'statusCode': 400, 'body': json.dumps({"error": "Role not found in token"}), "headers": headers}

    if role == "visitor":
        return {'statusCode': 403, 'body': json.dumps({"error": "Access denied: insufficient permissions"}), "headers": headers}

    return None