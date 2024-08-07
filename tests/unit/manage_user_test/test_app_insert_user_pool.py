import json
import unittest
from modules.manage_user.insert_user_pool import app

mock_body = {
    "body": json.dumps({
      "email": "bustosanna046@gmail.com",
      "phone_number": "7776048394",
      "user_name": "cristina",
      "password": "Cristina2002"
    })
}

class TestCreateUser(unittest.TestCase):
    def test_lambda_handler(self):
        result = app.lambda_handler(mock_body,None)
        print(result)


if __name__ == '__main__':
    unittest.main()
