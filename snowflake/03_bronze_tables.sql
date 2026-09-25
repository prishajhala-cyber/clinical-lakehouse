use role pipeline_role;
use warehouse lab_wh;
use database clinical;
use schema bronze;

create table if not exists fhir_patients (
  raw variant,
  source_file varchar,
  loaded_at timestamp_ntz
)
comment = 'Raw FHIR R4 Patient resources, one per row, exactly as received';

create table if not exists fhir_observations (
  raw variant,
  source_file varchar,
  loaded_at timestamp_ntz
)
comment = 'Raw FHIR R4 Observation resources, one per row, exactly as received';

create table if not exists hl7_observations (
  raw variant,
  source_file varchar,
  loaded_at timestamp_ntz
)
comment = 'HL7 v2 ORU^R01 lab results, parsed to JSON at ingestion';

show tables in schema bronze;