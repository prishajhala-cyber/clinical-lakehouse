use role pipeline_role;
use warehouse lab_wh;
use database clinical;

-- The Bronze schema holds the landing stage now and the raw tables in Step 4
create schema if not exists bronze;
use schema bronze;

-- Internal stage: Snowflake-managed storage for raw files (the S3 equivalent)
create stage if not exists landing
  comment = 'Raw files as received: FHIR NDJSON and HL7 v2 messages';

-- Tells Snowflake how to read JSON files; used when querying or loading them
create file format if not exists json_fmt
  type = json;

-- Should run without error and return no rows yet
list @landing;