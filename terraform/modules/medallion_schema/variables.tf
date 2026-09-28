variable "database" {
  description = "Existing database that will contain the schema"
  type        = string
}

variable "schema_name" {
  description = "Schema to create, in uppercase (e.g., LAB_GOLD)"
  type        = string
}

variable "comment" {
  description = "What this schema holds"
  type        = string
}

variable "writer_role" {
  description = "Role that builds objects in this schema (the pipeline)"
  type        = string
}

variable "warehouse" {
  description = "Warehouse the reader role may use for queries"
  type        = string
}