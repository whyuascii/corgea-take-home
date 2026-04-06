variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "aws_region" {
  description = "AWS region for this regional stack"
  type        = string
}

variable "is_primary" {
  description = "True for primary region, false for secondary/failover region"
  type        = bool
  default     = true
}

# --- Networking ---

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "availability_zones" {
  description = "Availability zones for subnets"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway instead of one per AZ"
  type        = bool
  default     = true
}

# --- Compute ---

variable "container_image" {
  description = "Docker image URI for the backend container"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

variable "ecs_task_cpu" {
  description = "CPU units for the ECS task"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory in MiB for the ECS task"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_min_count" {
  description = "Minimum ECS tasks for autoscaling"
  type        = number
  default     = 1
}

variable "ecs_max_count" {
  description = "Maximum ECS tasks for autoscaling"
  type        = number
  default     = 4
}

# --- Database ---

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
  default     = ""
  sensitive   = true
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  default     = ""
  sensitive   = true
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for RDS"
  type        = bool
  default     = true
}

variable "rds_source_arn" {
  description = "ARN of primary RDS instance for cross-region replica"
  type        = string
  default     = ""
}

variable "rds_replica_kms_key_arn" {
  description = "KMS key ARN for encrypting the cross-region replica"
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
  description = "Number of Redis cache nodes (>= 2 required for automatic failover)"
  type        = number
  default     = 2
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
  description = "Enable ElastiCache Global Datastore for cross-region"
  type        = bool
  default     = false
}

variable "redis_global_replication_group_id" {
  description = "Global replication group ID for secondary region to join"
  type        = string
  default     = ""
}

variable "redis_auth_token" {
  description = "Auth token for Redis (requires transit_encryption_enabled)"
  type        = string
  default     = ""
  sensitive   = true
}

# --- TLS / DNS ---

variable "alb_acm_certificate_arn" {
  description = "ACM certificate ARN for the ALB HTTPS listener"
  type        = string
}

# --- Secrets ---

variable "django_secret_key" {
  description = "Django SECRET_KEY"
  type        = string
  sensitive   = true
}

variable "field_encryption_key" {
  description = "Fernet encryption key for model fields"
  type        = string
  sensitive   = true
}

variable "resend_api_key" {
  description = "Resend API key"
  type        = string
  default     = ""
  sensitive   = true
}

variable "sentry_dsn" {
  description = "Sentry DSN"
  type        = string
  default     = ""
  sensitive   = true
}

variable "jira_api_token" {
  description = "Jira API token"
  type        = string
  default     = ""
  sensitive   = true
}

variable "linear_api_key" {
  description = "Linear API key"
  type        = string
  default     = ""
  sensitive   = true
}

# --- App Config (SSM) ---

variable "django_allowed_hosts" {
  description = "Comma-separated Django ALLOWED_HOSTS"
  type        = string
}

variable "cors_allowed_origins" {
  description = "Comma-separated CORS allowed origins"
  type        = string
  default     = ""
}

variable "data_retention_days" {
  description = "Days to retain finding/scan data"
  type        = number
  default     = 90
}

variable "max_login_attempts" {
  description = "Max failed login attempts before lockout"
  type        = number
  default     = 5
}

variable "lockout_window_minutes" {
  description = "Account lockout window in minutes"
  type        = number
  default     = 15
}

variable "trusted_proxies" {
  description = "Comma-separated trusted proxy IPs/CIDRs"
  type        = string
  default     = ""
}

variable "default_from_email" {
  description = "Default sender email address"
  type        = string
  default     = "noreply@vulntracker.corgea.com"
}

variable "vulntracker_base_url" {
  description = "Application base URL"
  type        = string
  default     = ""
}

# --- Optional ---

variable "log_group_kms_key_id" {
  description = "KMS key ARN for CloudWatch log encryption"
  type        = string
  default     = ""
}

variable "alb_access_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  type        = string
  default     = ""
}

variable "kms_key_arns" {
  description = "Map of KMS key name to ARN (keys: rds, secrets, s3, logs, cloudtrail)"
  type        = map(string)
  default     = {}
}

variable "enable_vpc_endpoints" {
  description = "Create VPC endpoints for AWS services"
  type        = bool
  default     = true
}

variable "enable_ip_reputation_rules" {
  description = "Enable AWS IP reputation list WAF rules"
  type        = bool
  default     = true
}

variable "enable_anonymous_ip_rules" {
  description = "Enable AWS anonymous IP list WAF rules"
  type        = bool
  default     = true
}

variable "enable_bot_control_rules" {
  description = "Enable AWS bot control WAF rules (count mode)"
  type        = bool
  default     = false
}

variable "enable_waf_logging" {
  description = "Enable WAF logging via Kinesis Firehose to S3"
  type        = bool
  default     = true
}

variable "sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarm notifications"
  type        = string
  default     = ""
}

# --- S3 / CDN ---

variable "cloudfront_distribution_arn" {
  description = "CloudFront distribution ARN for S3 bucket policy (set after CDN is created)"
  type        = string
  default     = ""
}

variable "s3_replication_destination_bucket_arn" {
  description = "Secondary region S3 bucket ARN for cross-region replication"
  type        = string
  default     = ""
}

variable "s3_replication_role_arn" {
  description = "IAM role ARN for S3 cross-region replication"
  type        = string
  default     = ""
}
