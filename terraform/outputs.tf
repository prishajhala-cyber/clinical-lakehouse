output "reader_roles" {
  description = "Read-only role for each medallion layer"
  value = {
    bronze = module.lab_bronze.reader_role_name
    silver = module.lab_silver.reader_role_name
    gold   = module.lab_gold.reader_role_name
  }
}