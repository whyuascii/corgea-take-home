resource "aws_wafv2_web_acl" "alb" {
  name        = "${local.name_prefix}-alb-waf"
  description = "WAF for ${local.name_prefix} ALB"
  scope       = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "AWSManagedRulesCommonRuleSet"
    priority = 1

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-common-rules"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-bad-inputs"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWSManagedRulesSQLiRuleSet"
    priority = 3

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-sqli-rules"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "RateLimitRule"
    priority = 4

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "${local.name_prefix}-rate-limit"
      sampled_requests_enabled   = true
    }
  }

  dynamic "rule" {
    for_each = var.enable_ip_reputation_rules ? [1] : []
    content {
      name     = "AWSManagedRulesAmazonIpReputationList"
      priority = 5

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          name        = "AWSManagedRulesAmazonIpReputationList"
          vendor_name = "AWS"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${local.name_prefix}-ip-reputation"
        sampled_requests_enabled   = true
      }
    }
  }

  dynamic "rule" {
    for_each = var.enable_anonymous_ip_rules ? [1] : []
    content {
      name     = "AWSManagedRulesAnonymousIpList"
      priority = 6

      override_action {
        none {}
      }

      statement {
        managed_rule_group_statement {
          name        = "AWSManagedRulesAnonymousIpList"
          vendor_name = "AWS"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${local.name_prefix}-anonymous-ip"
        sampled_requests_enabled   = true
      }
    }
  }

  dynamic "rule" {
    for_each = var.enable_bot_control_rules ? [1] : []
    content {
      name     = "AWSManagedRulesBotControlRuleSet"
      priority = 7

      override_action {
        count {}
      }

      statement {
        managed_rule_group_statement {
          name        = "AWSManagedRulesBotControlRuleSet"
          vendor_name = "AWS"
        }
      }

      visibility_config {
        cloudwatch_metrics_enabled = true
        metric_name                = "${local.name_prefix}-bot-control"
        sampled_requests_enabled   = true
      }
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-waf"
    sampled_requests_enabled   = true
  }

  tags = {
    Name = "${local.name_prefix}-alb-waf"
  }
}

resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.alb.arn
}

resource "aws_s3_bucket" "waf_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = "${local.name_prefix}-waf-logs"

  tags = {
    Name = "${local.name_prefix}-waf-logs"
  }
}

resource "aws_s3_bucket_versioning" "waf_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = aws_s3_bucket.waf_logs[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket" "waf_access_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = "${local.name_prefix}-waf-access-logs"

  tags = {
    Name = "${local.name_prefix}-waf-access-logs"
  }
}

resource "aws_s3_bucket_versioning" "waf_access_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = aws_s3_bucket.waf_access_logs[0].id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "waf_access_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = aws_s3_bucket.waf_access_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn != "" ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null
    }
    bucket_key_enabled = var.kms_key_arn != "" ? true : false
  }
}

resource "aws_s3_bucket_public_access_block" "waf_access_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = aws_s3_bucket.waf_access_logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "waf_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = aws_s3_bucket.waf_logs[0].id

  target_bucket = aws_s3_bucket.waf_access_logs[0].id
  target_prefix = "waf-logs-access/"
}

resource "aws_s3_bucket_public_access_block" "waf_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = aws_s3_bucket.waf_logs[0].id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "waf_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = aws_s3_bucket.waf_logs[0].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = var.kms_key_arn != "" ? "aws:kms" : "AES256"
      kms_master_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null
    }
    bucket_key_enabled = var.kms_key_arn != "" ? true : false
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "waf_logs" {
  count  = var.enable_waf_logging ? 1 : 0
  bucket = aws_s3_bucket.waf_logs[0].id

  rule {
    id     = "expire-old-logs"
    status = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    expiration {
      days = 90
    }
  }
}

resource "aws_iam_role" "waf_firehose" {
  count = var.enable_waf_logging ? 1 : 0

  name = "${local.name_prefix}-waf-firehose-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "firehose.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })

  tags = {
    Name = "${local.name_prefix}-waf-firehose-role"
  }
}

resource "aws_iam_role_policy" "waf_firehose" {
  count = var.enable_waf_logging ? 1 : 0

  name = "${local.name_prefix}-waf-firehose-s3"
  role = aws_iam_role.waf_firehose[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:AbortMultipartUpload",
          "s3:GetBucketLocation",
          "s3:GetObject",
          "s3:ListBucket",
          "s3:ListBucketMultipartUploads",
          "s3:PutObject",
        ]
        Resource = [
          aws_s3_bucket.waf_logs[0].arn,
          "${aws_s3_bucket.waf_logs[0].arn}/*",
        ]
      },
    ]
  })
}

resource "aws_kinesis_firehose_delivery_stream" "waf_logs" {
  count = var.enable_waf_logging ? 1 : 0

  name        = "aws-waf-logs-${local.name_prefix}"
  destination = "extended_s3"

  extended_s3_configuration {
    role_arn   = aws_iam_role.waf_firehose[0].arn
    bucket_arn = aws_s3_bucket.waf_logs[0].arn
    prefix     = "waf-logs/"

    buffering_size     = 5
    buffering_interval = 300
    compression_format = "GZIP"
  }

  tags = {
    Name = "aws-waf-logs-${local.name_prefix}"
  }
}

resource "aws_wafv2_web_acl_logging_configuration" "main" {
  count = var.enable_waf_logging ? 1 : 0

  log_destination_configs = [aws_kinesis_firehose_delivery_stream.waf_logs[0].arn]
  resource_arn            = aws_wafv2_web_acl.alb.arn
}
