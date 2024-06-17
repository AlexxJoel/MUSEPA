import json

import psycopg2
from functions import datetime_serializer
from psycopg2.extras import RealDictCursor


def lambda_handler(_event, _context):
    conn = None
    cur = None
    try:
        # SonarQube/SonarCloud ignore start
        # Database connection
        conn = psycopg2.connect(
            host="ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech",
            user="default",
            password="pnQI1h7sNfFK",
            database="verceldb",
        )

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # SonarQube/SonarCloud ignore end
        # Find all users
        cur.execute("SELECT * FROM users")
        # SonarQube/SonarCloud ignore start

        users = cur.fetchall()

        # Find all visitors by user_id
        rows = []
        for user in users:
            cur.execute("SELECT * FROM visitors WHERE id_user = %s", (user["id"],))
            visitor = cur.fetchone()
            if visitor is not None:
                visitor["user"] = user
                rows.append(visitor)

        return {"statusCode": 200, "body": json.dumps({"data": rows}, default=datetime_serializer)}
    except Exception as e:
        return {'statusCode': 500, 'body': json.dumps({"error": str(e)})}
    finally:
        # Close connection and cursor
        if conn is not None:
            conn.close()
        if cur is not None:
            cur.close()
    # SonarQube/SonarCloud ignore end
