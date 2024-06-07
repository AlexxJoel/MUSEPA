import sys
import logging
import pymysql
import os

# rds settings
user_name = os.environ['default']
password = os.environ['pnQI1h7sNfFK']
proxy_host = os.environ['ep-gentle-mode-a4hjun6w-pooler.us-east-1.aws.neon.tech']
db_name = os.environ['verceldb']

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# create the database connection outside of the handler to allow connections to be
# re-used by subsequent function invocations.

try:
    conn = pymysql.connect(host=proxy_host, user=user_name, passwd=password, db=db_name, connect_timeout=5)
except pymysql.MySQLError as e:
    logger.error("ERROR: Unexpected error: Could not connect to MySQL instance.")
    logger.error(e)
    sys.exit(1)

logger.info("SUCCESS: Connection to RDS for MySQL instance succeeded")


