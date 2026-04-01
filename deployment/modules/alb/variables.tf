variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_id" {
  description = "VPC ID"
  type        = string
}

variable "public_subnet_ids" {
  description = "Public subnet IDs for the ALB"
  type        = list(string)
}

variable "alb_security_group_id" {
  description = "Security group ID for the ALB"
  type        = string
}

variable "container_port" {
  description = "Port the backend container listens on"
  type        = number
  default     = 8000
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS"
  type        = string
}

variable "health_check_path" {
  description = "Health check path"
  type        = string
  default     = "/api/health/"
}

variable "health_check_interval" {
  description = "Seconds between health checks"
  type        = number
  default     = 30
}

variable "health_check_timeout" {
  description = "Health check timeout in seconds"
  type        = number
  default     = 5
}

variable "healthy_threshold" {
  description = "Consecutive healthy checks before marking healthy"
  type        = number
  default     = 2
}

variable "unhealthy_threshold" {
  description = "Consecutive unhealthy checks before marking unhealthy"
  type        = number
  default     = 3
}

variable "deregistration_delay" {
  description = "Seconds to wait before deregistering targets"
  type        = number
  default     = 30
}

variable "access_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  type        = string
  default     = ""
}

variable "access_logs_enabled" {
  description = "Enable ALB access logging"
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

variable "kms_key_arn" {
  description = "KMS key ARN for encrypting WAF log S3 bucket"
  type        = string
  default     = ""
}
