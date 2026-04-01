variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "is_primary" {
  description = "True for primary instance, false for cross-region read replica"
  type        = bool
  default     = true
}

variable "source_db_arn" {
  description = "ARN of the primary RDS instance (required when is_primary=false)"
  type        = string
  default     = ""
}

variable "replica_kms_key_arn" {
  description = "KMS key ARN for encrypting the replica (required for cross-region encrypted replicas)"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the DB subnet group"
  type        = list(string)
}

variable "rds_security_group_id" {
  description = "Security group ID for RDS"
  type        = string
}

variable "instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum storage for autoscaling in GB"
  type        = number
  default     = 100
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = ""
}

variable "db_username" {
  description = "Master username"
  type        = string
  default     = ""
  sensitive   = true
}

variable "db_password" {
  description = "Master password (auto-generated if empty)"
  type        = string
  default     = ""
  sensitive   = true
}

variable "multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Days to retain automated backups"
  type        = number
  default     = 7
}

variable "deletion_protection" {
  description = "Enable deletion protection"
  type        = bool
  default     = false
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot on deletion"
  type        = bool
  default     = true
}

variable "performance_insights_enabled" {
  description = "Enable Performance Insights"
  type        = bool
  default     = true
}

variable "kms_key_arn" {
  description = "Customer-managed KMS key ARN for storage encryption"
  type        = string
  default     = ""
}
