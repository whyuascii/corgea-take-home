variable "domain_name" {
  description = "Primary domain name (e.g., vulntracker.corgea.com)"
  type        = string
  default     = "vulntracker.corgea.com"
}

variable "api_domain_name" {
  description = "API domain name (e.g., api.vulntracker.corgea.com)"
  type        = string
  default     = "api.vulntracker.corgea.com"
}

variable "hosted_zone_id" {
  description = "Route 53 hosted zone ID for DNS records"
  type        = string
  default     = ""
}

# CloudFront requires us-east-1 certificate
variable "acm_certificate_arn" {
  description = "ACM certificate ARN for CloudFront (must be in us-east-1)"
  type        = string
  default     = "arn:aws:acm:us-east-1:123456789012:certificate/placeholder-cert-id"
}

variable "primary_alb_acm_certificate_arn" {
  description = "ACM certificate ARN for the primary region ALB"
  type        = string
  default     = "arn:aws:acm:us-east-1:123456789012:certificate/placeholder-alb-cert-id"
}

variable "secondary_alb_acm_certificate_arn" {
  description = "ACM certificate ARN for the secondary region ALB"
  type        = string
  default     = ""
}

variable "log_group_kms_key_id" {
  description = "KMS key ARN for encrypting CloudWatch log groups"
  type        = string
  default     = ""
}

variable "alb_access_logs_bucket" {
  description = "S3 bucket for ALB access logs"
  type        = string
  default     = ""
}
