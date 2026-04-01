variable "enable_guardduty" {
  description = "Enable Amazon GuardDuty threat detection"
  type        = bool
  default     = true
}

variable "enable_security_hub" {
  description = "Enable AWS Security Hub with Foundational Best Practices"
  type        = bool
  default     = true
}

variable "enable_cloudtrail" {
  description = "Enable AWS CloudTrail for API audit logging"
  type        = bool
  default     = true
}

variable "enable_aws_config" {
  description = "Enable AWS Config for resource compliance tracking"
  type        = bool
  default     = true
}

variable "enable_vpc_endpoints" {
  description = "Create VPC endpoints for AWS services (S3, ECR, Secrets Manager, etc.)"
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
  description = "Enable AWS bot control WAF rules (count mode — high false-positive risk)"
  type        = bool
  default     = false
}

variable "enable_waf_logging" {
  description = "Enable WAF logging via Kinesis Firehose to S3"
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Email address for security and operational alert notifications"
  type        = string
  default     = ""
}
