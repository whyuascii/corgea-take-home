variable "app_name" {
  description = "Application name used for resource naming and tagging"
  type        = string
  default     = "vulntracker"
}

variable "environment" {
  description = "Deployment environment"
  type        = string

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "enable_cross_region" {
  description = "Enable cross-region failover with secondary region stack"
  type        = bool
  default     = false
}
