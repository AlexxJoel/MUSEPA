import unittest
import json
from modules.manage_user.set_password import app

mock_body = {
    "body":json.dumps({
        "username":"prueba",
        "temporary_password":"Anna2002",
        "new_password":"Jimin2002"
    })
}


class TestSetPassword(unittest.TestCase):
    def test_lambda_handler(selfs):
        result= app.lambda_handler(mock_body,None)
        print(result)


if __name__ == '__main__':
    unittest.main()
