variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "hosted_zone_id" {
  description = "Route 53 hosted zone ID"
  type        = string
}

variable "domain_name" {
  description = "Frontend domain name"
  type        = string
}

variable "api_domain_name" {
  description = "API domain name"
  type        = string
}

variable "primary_alb_dns_name" {
  description = "Primary region ALB DNS name"
  type        = string
}

variable "primary_alb_zone_id" {
  description = "Primary region ALB Route53 zone ID"
  type        = string
}

variable "secondary_alb_dns_name" {
  description = "Secondary region ALB DNS name (empty to disable failover)"
  type        = string
  default     = ""
}

variable "secondary_alb_zone_id" {
  description = "Secondary region ALB Route53 zone ID"
  type        = string
  default     = ""
}

variable "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  type        = string
}

variable "cloudfront_zone_id" {
  description = "CloudFront hosted zone ID (always Z2FDTNDATAQYW2)"
  type        = string
  default     = "Z2FDTNDATAQYW2"
}
