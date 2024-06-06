import pymysql
import json
from commons.database import conn, logger


def get_events():
    try:
        with conn.cursor() as cursor:
            sql = "SELECT * FROM events"
            cursor.execute(sql)
            return cursor.fetchall()
    except pymysql.MySQLError as e:
        logger.error("ERROR: Could not retrieve events.")
        logger.error(e)
        return None  # Indicate error
    finally:
        conn.close()

def lambda_handler(event, context):
    events = get_events()

    if events is None:
        # Handle error case (e.g., log or return specific error message)
        return {
            "statusCode": 500,
            "body": json.dumps({"message": "Error retrieving events."})
        }

    # Success case: include retrieved events in the body
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Events retrieved successfully.",
            "data": events
        }),
    }


if __name__ == "__main__":
    get_events()  # For testing purposes

