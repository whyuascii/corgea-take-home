variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

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

variable "alert_email" {
  description = "Email address for security alert notifications"
  type        = string
  default     = ""
}

variable "kms_key_arns" {
  description = "Map of KMS key name to ARN (keys: s3, logs, cloudtrail)"
  type        = map(string)
  default     = {}
}
