from unittest.mock import patch
from botocore.exceptions import ClientError

from modules.visitors.create_visitor import app

import unittest
import json

mock_body = {
    "email": "RE@example.com",
    "password": "MORE123",
    "username": "MORE3e",
    "id_role": 2,
    "name": "Alejandro",
    "surname": "Morellano",
    "lastname": "Alvarez"
}


class TestCreateVisitor(unittest.TestCase):
    @patch.dict("os.environ", {"HOST": "localhost", "DATABASE": "test", "USER": "test", "PASSWORD": "test"})
    @patch("modules.visitors.create_visitor.app.validate_connection")
    @patch("modules.visitors.create_visitor.app.validate_event_body")
    @patch("modules.visitors.create_visitor.app.validate_payload")
    @patch("modules.visitors.create_visitor.app.execute")
    @patch("modules.visitors.create_visitor.app.fetchone")
    @patch("modules.visitors.create_visitor.app.commit")
    @patch("modules.visitors.create_visitor.app.close")
    def test_create_visitor(self, mock_commit, mock_fetchone, mock_execute, mock_validate_payload, mock_validate_event_body,
                            mock_validate_connection, mock_close):
        mock_validate_connection.return_value = True
        mock_validate_event_body.return_value = True
        mock_validate_payload.return_value = True

        mock_execute.return_value = True
        mock_fetchone.return_value = {"id": 1}
        mock_commit.return_value = True

        response = app.lambda_handler({"body": json.dumps(mock_body)}, {})
        self.assertEqual(response['statusCode'], 200)
        self.assertEqual(json.loads(response['body']), {"message": "Visitor created successfully"})
        mock_close.assert_called_once_with(True)


if __name__ == '__main__':
    unittest.main()






    
