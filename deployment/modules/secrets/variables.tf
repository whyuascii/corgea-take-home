variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "django_secret_key" {
  description = "Django SECRET_KEY for cryptographic signing"
  type        = string
  sensitive   = true
}

variable "field_encryption_key" {
  description = "Fernet key for encrypting sensitive model fields"
  type        = string
  sensitive   = true
}

variable "resend_api_key" {
  description = "Resend API key for transactional email"
  type        = string
  default     = ""
  sensitive   = true
}

variable "postgres_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "database_url" {
  description = "Full PostgreSQL connection URL"
  type        = string
  sensitive   = true
}

variable "redis_url" {
  description = "Full Redis connection URL"
  type        = string
  sensitive   = true
}

variable "sentry_dsn" {
  description = "Sentry DSN for error tracking"
  type        = string
  default     = ""
  sensitive   = true
}

variable "jira_api_token" {
  description = "Jira API token for integration"
  type        = string
  default     = ""
  sensitive   = true
}

variable "linear_api_key" {
  description = "Linear API key for integration"
  type        = string
  default     = ""
  sensitive   = true
}

variable "allowed_hosts" {
  description = "Comma-separated Django ALLOWED_HOSTS"
  type        = string

  validation {
    condition     = var.allowed_hosts != "*"
    error_message = "ALLOWED_HOSTS must not be wildcard '*'."
  }
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

variable "kms_key_id" {
  description = "Customer-managed KMS key ARN for encrypting secrets"
  type        = string
  default     = ""
}
