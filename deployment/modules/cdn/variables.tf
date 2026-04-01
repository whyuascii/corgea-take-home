variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "domain_name" {
  description = "Primary domain name for CloudFront"
  type        = string
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN (must be in us-east-1)"
  type        = string
}

variable "primary_alb_dns_name" {
  description = "Primary region ALB DNS name"
  type        = string
}

variable "secondary_alb_dns_name" {
  description = "Secondary region ALB DNS name (empty to disable failover)"
  type        = string
  default     = ""
}

variable "primary_bucket_domain_name" {
  description = "Primary region S3 bucket regional domain name"
  type        = string
}

variable "secondary_bucket_domain_name" {
  description = "Secondary region S3 bucket regional domain name (empty to disable failover)"
  type        = string
  default     = ""
}

variable "default_ttl" {
  description = "Default TTL for cached objects in seconds"
  type        = number
  default     = 86400
}

variable "max_ttl" {
  description = "Maximum TTL for cached objects in seconds"
  type        = number
  default     = 604800
}

variable "price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "web_acl_id" {
  description = "WAF Web ACL ARN to associate with the CloudFront distribution (must be CLOUDFRONT scope)"
  type        = string
  default     = ""
}

variable "enable_access_logging" {
  description = "Enable CloudFront access logging to S3"
  type        = bool
  default     = true
}
