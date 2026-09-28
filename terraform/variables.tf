variable "organization_name" {
  description = "Snowflake organization name (first part of the account identifier)"
  type        = string
}

variable "account_name" {
  description = "Snowflake account name (second part of the account identifier)"
  type        = string
}

variable "terraform_user" {
  description = "Snowflake user Terraform logs in as"
  type        = string
  default     = "TERRAFORM_USER"
}

variable "private_key_path" {
  description = "Path to the private key for key-pair login"
  type        = string
}

variable "my_username" {
  description = "Your own Snowflake username, granted Gold read access for testing"
  type        = string
}

variable "database" {
  type    = string
  default = "CLINICAL"
}

variable "warehouse" {
  type    = string
  default = "LAB_WH"
}

variable "pipeline_role" {
  type    = string
  default = "PIPELINE_ROLE"
}