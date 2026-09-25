select current_user()
use role accountadmin;

-- Compute: the smallest warehouse, which pauses itself after 60 idle seconds
create warehouse if not exists lab_wh
  warehouse_size = xsmall
  auto_suspend = 60
  auto_resume = true
  initially_suspended = true;

-- Storage: the database that will hold Bronze, Silver, and Gold
create database if not exists clinical;

-- A dedicated role with only the permissions the pipeline needs
create role if not exists pipeline_role;
grant usage on warehouse lab_wh to role pipeline_role;
grant usage, create schema on database clinical to role pipeline_role;

-- A service user for programs, logging in with your public key
create user if not exists pipeline_user
  type = service
  default_role = pipeline_role
  default_warehouse = lab_wh
  rsa_public_key = '<randompublickey>';

grant role pipeline_role to user pipeline_user;

-- Let yourself switch into the pipeline role in worksheets
grant role pipeline_role to user PRISHAJHALA12345;