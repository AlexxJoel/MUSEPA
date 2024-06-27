import json
import unittest
from modules.manage_user.login import app

mock_body = {
    "body": json.dumps({
        "username":'Cris',
        "password":"asdasd"
    })
}

class TestLogin(unittest.TestCase):
    def test_lambda_handler(self):
        result = app.lambda_handler(mock_body,None)
        print(result)


if __name__ == '__main__':
    unittest.main()
