provider "snowflake" {
  organization_name = var.organization_name
  account_name      = var.account_name
  user              = var.terraform_user
  authenticator     = "SNOWFLAKE_JWT"
  private_key       = file(pathexpand(var.private_key_path))
  role              = "ACCOUNTADMIN"
  warehouse         = var.warehouse
}