"""Orchestrate the clinical lakehouse with Airflow.

Airflow runs in its own environment, so every task calls Python and dbt from
the "clinical" environment by full path. Airflow only coordinates: the real
work happens in the ingestion scripts, Snowflake, and dbt.
"""
from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag

PROJECT = "/Users/prishajhala/clinical-lakehouse"
PYTHON = "/opt/anaconda3/envs/clinical/bin/python"
DBT = "/opt/anaconda3/envs/clinical/bin/dbt"


def run_python(code):
    """Build a shell command that runs one line of Python in the clinical env."""
    return f'cd {PROJECT}/ingest && {PYTHON} -c "{code}"'


@dag(
    dag_id="clinical_lakehouse",
    description="Land files, load Bronze, and build Silver and Gold with dbt",
    schedule=None,
    start_date=datetime(2026, 1, 1),
    catchup=False,
    default_args={"retries": 2, "retry_delay": timedelta(minutes=1)},
    tags=["clinical", "practice"],
)
def clinical_lakehouse():

    # ---------- Landing: upload raw files to the Snowflake stage ----------
    upload_fhir = BashOperator(
        task_id="upload_fhir",
        bash_command=run_python("import ingest; ingest.upload_fhir()"),
    )
    upload_hl7 = BashOperator(
        task_id="upload_hl7",
        bash_command=run_python("import ingest; ingest.upload_hl7()"),
    )

    # ---------- Bronze: COPY INTO each raw table ----------
    load_fhir_patients = BashOperator(
        task_id="load_fhir_patients",
        bash_command=run_python("import load_bronze; load_bronze.load_table('fhir_patients')"),
    )
    load_fhir_observations = BashOperator(
        task_id="load_fhir_observations",
        bash_command=run_python("import load_bronze; load_bronze.load_table('fhir_observations')"),
    )
    load_hl7_observations = BashOperator(
        task_id="load_hl7_observations",
        bash_command=run_python("import load_bronze; load_bronze.load_table('hl7_observations')"),
    )

    # ---------- Silver and Gold: dbt builds models and runs tests ----------
    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"cd {PROJECT}/clinical_dbt && "
            f"set -a && source ../.env && set +a && "
            f"{DBT} build"
        ),
    )

    # ---------- Dependencies ----------
    upload_fhir >> [load_fhir_patients, load_fhir_observations]
    upload_hl7 >> load_hl7_observations
    [load_fhir_patients, load_fhir_observations, load_hl7_observations] >> dbt_build


clinical_lakehouse()