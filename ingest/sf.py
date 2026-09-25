"""Shared Snowflake connection used by every pipeline script."""
import os
import pathlib

import snowflake.connector
from dotenv import load_dotenv

ROOT = pathlib.Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")


def connect():
    """Open a Snowflake connection using key-pair authentication."""
    return snowflake.connector.connect(
        account=os.environ["SNOWFLAKE_ACCOUNT"],
        user=os.environ["SNOWFLAKE_USER"],
        authenticator="SNOWFLAKE_JWT",
        private_key_file=os.environ["SNOWFLAKE_KEY_PATH"],
        role="PIPELINE_ROLE",
        warehouse="LAB_WH",
        database="CLINICAL",
        schema="BRONZE",
    )