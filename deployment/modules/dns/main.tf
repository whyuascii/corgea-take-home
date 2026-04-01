locals {
  name_prefix  = "${var.app_name}-${var.environment}"
  has_failover = var.secondary_alb_dns_name != ""
}

# Health check on primary ALB — Route 53 uses this to trigger failover
resource "aws_route53_health_check" "primary" {
  fqdn              = var.primary_alb_dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/api/health/"
  failure_threshold = 3
  request_interval  = 10
  measure_latency   = true

  tags = {
    Name = "${local.name_prefix}-primary-health"
  }
}

resource "aws_route53_health_check" "secondary" {
  count = local.has_failover ? 1 : 0

  fqdn              = var.secondary_alb_dns_name
  port              = 443
  type              = "HTTPS"
  resource_path     = "/api/health/"
  failure_threshold = 3
  request_interval  = 10
  measure_latency   = true

  tags = {
    Name = "${local.name_prefix}-secondary-health"
  }
}

# API domain — failover routing between primary and secondary ALBs
resource "aws_route53_record" "api_primary" {
  zone_id = var.hosted_zone_id
  name    = var.api_domain_name
  type    = "A"

  alias {
    name                   = var.primary_alb_dns_name
    zone_id                = var.primary_alb_zone_id
    evaluate_target_health = true
  }

  set_identifier  = "primary"
  health_check_id = aws_route53_health_check.primary.id

  failover_routing_policy {
    type = "PRIMARY"
  }
}

resource "aws_route53_record" "api_secondary" {
  count = local.has_failover ? 1 : 0

  zone_id = var.hosted_zone_id
  name    = var.api_domain_name
  type    = "A"

  alias {
    name                   = var.secondary_alb_dns_name
    zone_id                = var.secondary_alb_zone_id
    evaluate_target_health = true
  }

  set_identifier  = "secondary"
  health_check_id = aws_route53_health_check.secondary[0].id

  failover_routing_policy {
    type = "SECONDARY"
  }
}

# Frontend domain — points to CloudFront
resource "aws_route53_record" "frontend" {
  zone_id = var.hosted_zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = var.cloudfront_domain_name
    zone_id                = var.cloudfront_zone_id
    evaluate_target_health = false
  }
}
