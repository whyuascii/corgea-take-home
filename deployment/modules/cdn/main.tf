locals {
  name_prefix  = "${var.app_name}-${var.environment}"
  has_failover = var.secondary_alb_dns_name != "" && var.secondary_bucket_domain_name != ""
}

resource "aws_cloudfront_origin_access_control" "frontend" {
  name                              = "${local.name_prefix}-frontend-oac"
  description                       = "OAC for ${local.name_prefix} frontend"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_response_headers_policy" "security_headers" {
  name    = "${local.name_prefix}-security-headers"
  comment = "Security headers for ${local.name_prefix}"

  security_headers_config {
    content_type_options {
      override = true
    }

    frame_options {
      frame_option = "DENY"
      override     = true
    }

    strict_transport_security {
      access_control_max_age_sec = 63072000
      include_subdomains         = true
      preload                    = true
      override                   = true
    }

    content_security_policy {
      content_security_policy = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'"
      override                = true
    }

    referrer_policy {
      referrer_policy = "strict-origin-when-cross-origin"
      override        = true
    }
  }
}

resource "aws_s3_bucket" "cdn_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = "${local.name_prefix}-cdn-access-logs"

  tags = {
    Name = "${local.name_prefix}-cdn-access-logs"
  }
}

resource "aws_s3_bucket_versioning" "cdn_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = aws_s3_bucket.cdn_logs[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "cdn_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = aws_s3_bucket.cdn_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_ownership_controls" "cdn_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = aws_s3_bucket.cdn_logs[0].id

  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "cdn_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = aws_s3_bucket.cdn_logs[0].id
  acl    = "log-delivery-write"

  depends_on = [aws_s3_bucket_ownership_controls.cdn_logs]
}

resource "aws_s3_bucket_public_access_block" "cdn_logs" {
  count  = var.enable_access_logging ? 1 : 0
  bucket = aws_s3_bucket.cdn_logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "${local.name_prefix} distribution"
  aliases             = [var.domain_name]
  price_class         = var.price_class
  wait_for_deployment = false
  web_acl_id          = var.web_acl_id != "" ? var.web_acl_id : null

  dynamic "logging_config" {
    for_each = var.enable_access_logging ? [1] : []
    content {
      include_cookies = false
      bucket          = aws_s3_bucket.cdn_logs[0].bucket_domain_name
      prefix          = "cdn/"
    }
  }

  origin {
    domain_name              = var.primary_bucket_domain_name
    origin_id                = "s3-primary"
    origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
  }

  dynamic "origin" {
    for_each = local.has_failover ? [1] : []
    content {
      domain_name              = var.secondary_bucket_domain_name
      origin_id                = "s3-secondary"
      origin_access_control_id = aws_cloudfront_origin_access_control.frontend.id
    }
  }

  origin {
    domain_name = var.primary_alb_dns_name
    origin_id   = "alb-primary"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  dynamic "origin" {
    for_each = local.has_failover ? [1] : []
    content {
      domain_name = var.secondary_alb_dns_name
      origin_id   = "alb-secondary"

      custom_origin_config {
        http_port              = 80
        https_port             = 443
        origin_protocol_policy = "https-only"
        origin_ssl_protocols   = ["TLSv1.2"]
      }
    }
  }

  # S3 failover includes 403/404 because OAC returns 403 for missing objects
  dynamic "origin_group" {
    for_each = local.has_failover ? [1] : []
    content {
      origin_id = "s3-failover"

      failover_criteria {
        status_codes = [403, 404, 500, 502, 503, 504]
      }

      member {
        origin_id = "s3-primary"
      }

      member {
        origin_id = "s3-secondary"
      }
    }
  }

  dynamic "origin_group" {
    for_each = local.has_failover ? [1] : []
    content {
      origin_id = "alb-failover"

      failover_criteria {
        status_codes = [500, 502, 503, 504]
      }

      member {
        origin_id = "alb-primary"
      }

      member {
        origin_id = "alb-secondary"
      }
    }
  }

  default_cache_behavior {
    allowed_methods            = ["GET", "HEAD", "OPTIONS"]
    cached_methods             = ["GET", "HEAD"]
    target_origin_id           = local.has_failover ? "s3-failover" : "s3-primary"
    viewer_protocol_policy     = "redirect-to-https"
    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = var.default_ttl
    max_ttl     = var.max_ttl
  }

  ordered_cache_behavior {
    path_pattern               = "/api/*"
    allowed_methods            = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods             = ["GET", "HEAD"]
    target_origin_id           = local.has_failover ? "alb-failover" : "alb-primary"
    viewer_protocol_policy     = "redirect-to-https"
    compress                   = true
    response_headers_policy_id = aws_cloudfront_response_headers_policy.security_headers.id

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Host", "Origin", "Accept"]
      cookies {
        forward = "all"
      }
    }

    min_ttl     = 0
    default_ttl = 0
    max_ttl     = 0
  }

  # SPA routing — serve index.html for missing paths
  custom_error_response {
    error_code         = 403
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code         = 404
    response_code      = 200
    response_page_path = "/index.html"
  }

  custom_error_response {
    error_code            = 500
    response_code         = 500
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  viewer_certificate {
    acm_certificate_arn      = var.acm_certificate_arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  tags = {
    Name = "${local.name_prefix}-cdn"
  }
}
