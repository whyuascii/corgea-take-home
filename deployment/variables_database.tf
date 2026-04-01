# --- RDS ---

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "vulntracker"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "vulntracker"
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password (auto-generated if empty)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = false
}

variable "secondary_db_instance_class" {
  description = "RDS instance class for the secondary region replica"
  type        = string
  default     = "db.t3.micro"
}

variable "rds_replica_kms_key_arn" {
  description = "KMS key ARN in the secondary region for encrypting the RDS replica"
  type        = string
  default     = ""
}

# --- Redis ---

variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "redis_num_cache_nodes" {
  description = "Number of Redis cache nodes"
  type        = number
  default     = 1
}

variable "redis_snapshot_retention_limit" {
  description = "Days to retain Redis snapshots"
  type        = number
  default     = 7
}

variable "redis_snapshot_window" {
  description = "Daily snapshot time window (UTC)"
  type        = string
  default     = "05:00-06:00"
}

variable "enable_global_datastore" {
  description = "Enable ElastiCache Global Datastore for cross-region Redis"
  type        = bool
  default     = false
}
