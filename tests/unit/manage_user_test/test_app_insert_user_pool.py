import json
import unittest
from modules.manage_user.insert_user_pool import app

mock_body = {
    "body": json.dumps({
      "email": "example@example.com",
      "password": "your_password",
      "username": "your_username",
      "id_role": 1,
      "name": "your_name",
      "surname": "your_surname",
      "lastname": "your_lastname",
      "phone_number": "your_phone_number",
      "address": "your_address",
      "birthdate": "your_birthdate"
    })
}

class TestCreateUser(unittest.TestCase):
    def test_lambda_handler(self):
        result = app.lambda_handler(mock_body,None)
        print(result)


if __name__ == '__main__':
    unittest.main()
