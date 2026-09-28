# ---------- The schema ----------

resource "snowflake_schema" "this" {
  database = var.database
  name     = var.schema_name
  comment  = var.comment
}

# ---------- A read-only role for this layer ----------

resource "snowflake_account_role" "reader" {
  name    = "${var.schema_name}_READER"
  comment = "Read-only access to ${var.database}.${var.schema_name} (managed by Terraform)"
}

# ---------- The pipeline can build objects here ----------

resource "snowflake_grant_privileges_to_account_role" "writer_schema" {
  account_role_name = var.writer_role
  privileges        = ["USAGE", "CREATE TABLE", "CREATE VIEW", "CREATE STAGE", "CREATE FILE FORMAT"]
  on_schema {
    schema_name = snowflake_schema.this.fully_qualified_name
  }
}

# ---------- The reader can see the database, schema, and warehouse ----------

resource "snowflake_grant_privileges_to_account_role" "reader_database" {
  account_role_name = snowflake_account_role.reader.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "DATABASE"
    object_name = var.database
  }
}

resource "snowflake_grant_privileges_to_account_role" "reader_warehouse" {
  account_role_name = snowflake_account_role.reader.name
  privileges        = ["USAGE"]
  on_account_object {
    object_type = "WAREHOUSE"
    object_name = var.warehouse
  }
}

resource "snowflake_grant_privileges_to_account_role" "reader_schema" {
  account_role_name = snowflake_account_role.reader.name
  privileges        = ["USAGE"]
  on_schema {
    schema_name = snowflake_schema.this.fully_qualified_name
  }
}

# ---------- The reader can SELECT every table and view created here in the future ----------

resource "snowflake_grant_privileges_to_account_role" "reader_future_tables" {
  account_role_name = snowflake_account_role.reader.name
  privileges        = ["SELECT"]
  on_schema_object {
    future {
      object_type_plural = "TABLES"
      in_schema          = snowflake_schema.this.fully_qualified_name
    }
  }
}

resource "snowflake_grant_privileges_to_account_role" "reader_future_views" {
  account_role_name = snowflake_account_role.reader.name
  privileges        = ["SELECT"]
  on_schema_object {
    future {
      object_type_plural = "VIEWS"
      in_schema          = snowflake_schema.this.fully_qualified_name
    }
  }
}