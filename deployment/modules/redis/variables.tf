variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "is_primary" {
  description = "True for primary region, false for secondary"
  type        = bool
  default     = true
}

variable "enable_global_datastore" {
  description = "Enable ElastiCache Global Datastore for cross-region replication"
  type        = bool
  default     = false
}

variable "global_replication_group_id" {
  description = "Global replication group ID to join (required when is_primary=false and enable_global_datastore=true)"
  type        = string
  default     = ""
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for the ElastiCache subnet group"
  type        = list(string)
}

variable "redis_security_group_id" {
  description = "Security group ID for Redis"
  type        = string
}

variable "node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.micro"
}

variable "num_cache_nodes" {
  description = "Number of cache nodes (>= 2 required for automatic failover)"
  type        = number
  default     = 2
}

variable "engine_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.1"
}

variable "port" {
  description = "Redis port"
  type        = number
  default     = 6379
}

variable "snapshot_retention_limit" {
  description = "Days to retain automatic snapshots (0 = disabled)"
  type        = number
  default     = 7
}

variable "snapshot_window" {
  description = "Daily snapshot time window (UTC)"
  type        = string
  default     = "05:00-06:00"
}

variable "maintenance_window" {
  description = "Weekly maintenance window"
  type        = string
  default     = "sun:06:00-sun:07:00"
}

variable "auth_token" {
  description = "Auth token for Redis (requires transit_encryption_enabled). 16-128 chars, only printable ASCII excluding /, \", and @"
  type        = string
  default     = ""
  sensitive   = true
}

variable "automatic_failover_enabled" {
  description = "Enable automatic failover (requires num_cache_nodes >= 2)"
  type        = bool
  default     = true
}
