import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv(".env")

conn = snowflake.connector.connect(
    account=os.environ["SNOWFLAKE_ACCOUNT"],
    user=os.environ["SNOWFLAKE_USER"],
    authenticator="SNOWFLAKE_JWT",
    private_key_file=os.environ["SNOWFLAKE_KEY_PATH"],
    role="PIPELINE_ROLE",
    warehouse="LAB_WH",
)
row = conn.cursor().execute(
    "select current_user(), current_role(), current_warehouse()"
).fetchone()
print(row)
conn.close()