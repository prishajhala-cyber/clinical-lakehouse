"""Orchestrate the clinical lakehouse with Dagster.

Every piece of data is an asset: staged files, Bronze tables, and each dbt
model, so the lineage runs from raw files to Gold in one graph.

Run from the project root:
    dagster dev -f orchestration/dagster_defs.py
"""
import pathlib
import sys

from dagster import (
    AssetExecutionContext,
    AssetSelection,
    Definitions,
    ScheduleDefinition,
    asset,
    define_asset_job,
)
from dagster_dbt import DbtCliResource, DbtProject, dbt_assets

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / "ingest"))

import ingest  # noqa: E402
import load_bronze  # noqa: E402


# ---------- Landing: raw files in the Snowflake stage ----------

@asset(group_name="landing", description="FHIR NDJSON files uploaded to the @landing stage")
def landing_fhir_files():
    ingest.upload_fhir()


@asset(group_name="landing", description="HL7 v2 messages, raw and parsed, uploaded to @landing")
def landing_hl7_files():
    ingest.upload_hl7()


# ---------- Bronze: Snowflake tables loaded with COPY INTO ----------
# key_prefix "bronze" + the function name gives keys like bronze/fhir_patients,
# which match the dbt sources. That match is how Dagster links these assets
# to the dbt models that read them.

@asset(key_prefix="bronze", group_name="bronze", deps=[landing_fhir_files],
       description="Raw FHIR Patient resources")
def fhir_patients():
    load_bronze.load_table("fhir_patients")


@asset(key_prefix="bronze", group_name="bronze", deps=[landing_fhir_files],
       description="Raw FHIR Observation resources")
def fhir_observations():
    load_bronze.load_table("fhir_observations")


@asset(key_prefix="bronze", group_name="bronze", deps=[landing_hl7_files],
       description="Parsed HL7 v2 lab results")
def hl7_observations():
    load_bronze.load_table("hl7_observations")


# ---------- Silver and Gold: every dbt model becomes an asset ----------

dbt_project = DbtProject(
    project_dir=ROOT / "clinical_dbt",
    profiles_dir=ROOT / "clinical_dbt",
)
dbt_project.prepare_if_dev()


@dbt_assets(manifest=dbt_project.manifest_path)
def clinical_dbt_models(context: AssetExecutionContext, dbt: DbtCliResource):
    # "build" runs models and their tests in order. A failed test stops
    # downstream models from building on bad data.
    yield from dbt.cli(["build"], context=context).stream()


# ---------- Job and schedule ----------

full_pipeline = define_asset_job(
    name="full_pipeline",
    selection=AssetSelection.all(),
    description="Land files, load Bronze, and build Silver and Gold",
)

daily_refresh = ScheduleDefinition(
    job=full_pipeline,
    cron_schedule="0 6 * * *",  # every day at 6:00 AM
)


# ---------- Everything Dagster should know about ----------

defs = Definitions(
    assets=[
        landing_fhir_files,
        landing_hl7_files,
        fhir_patients,
        fhir_observations,
        hl7_observations,
        clinical_dbt_models,
    ],
    jobs=[full_pipeline],
    schedules=[daily_refresh],
    resources={"dbt": DbtCliResource(project_dir=dbt_project)},
)