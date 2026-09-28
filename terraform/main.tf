# The CLINICAL database, LAB_WH warehouse, and PIPELINE_ROLE already exist
# (created by the SQL setup scripts), so Terraform references them by name
# rather than managing them.

module "lab_bronze" {
  source      = "./modules/medallion_schema"
  database    = var.database
  schema_name = "LAB_BRONZE"
  comment     = "Raw plate reader exports and run metadata, loaded as received"
  writer_role = var.pipeline_role
  warehouse   = var.warehouse
}

module "lab_silver" {
  source      = "./modules/medallion_schema"
  database    = var.database
  schema_name = "LAB_SILVER"
  comment     = "Plate readings in long format, joined to LIMS plate maps"
  writer_role = var.pipeline_role
  warehouse   = var.warehouse
}

module "lab_gold" {
  source      = "./modules/medallion_schema"
  database    = var.database
  schema_name = "LAB_GOLD"
  comment     = "Plate QC and normalized binding results per design, ready for modeling"
  writer_role = var.pipeline_role
  warehouse   = var.warehouse
}

# Give yourself Gold read access, to test least privilege in Step 7
resource "snowflake_grant_account_role" "me_gold_reader" {
  role_name = module.lab_gold.reader_role_name
  user_name = var.my_username
}