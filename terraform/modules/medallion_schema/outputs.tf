output "schema_name" {
  description = "Name of the schema this module created"
  value       = snowflake_schema.this.name
}

output "reader_role_name" {
  description = "Name of the read-only role for this schema"
  value       = snowflake_account_role.reader.name
}