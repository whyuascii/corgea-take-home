locals {
  name_prefix = "${var.app_name}-${var.environment}"
}

module "vpc" {
  source = "../vpc"

  app_name             = var.app_name
  environment          = var.environment
  vpc_cidr             = var.vpc_cidr
  availability_zones   = var.availability_zones
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  container_port       = var.container_port
  single_nat_gateway   = var.single_nat_gateway
  log_group_kms_key_id = lookup(var.kms_key_arns, "logs", var.log_group_kms_key_id)
  enable_vpc_endpoints = var.enable_vpc_endpoints
  aws_region           = var.aws_region
}

module "secrets" {
  source = "../secrets"

  app_name    = var.app_name
  environment = var.environment

  django_secret_key    = var.django_secret_key
  field_encryption_key = var.field_encryption_key
  resend_api_key       = var.resend_api_key
  postgres_password    = module.rds.password
  database_url         = "postgres://${var.db_username}:${module.rds.password}@${module.rds.endpoint}:5432/${var.db_name}"
  redis_url            = "rediss://${module.redis.endpoint}:${module.redis.port}/0"
  sentry_dsn           = var.sentry_dsn
  jira_api_token       = var.jira_api_token
  linear_api_key       = var.linear_api_key
  kms_key_id           = lookup(var.kms_key_arns, "secrets", "")

  allowed_hosts          = var.django_allowed_hosts
  cors_allowed_origins   = var.cors_allowed_origins
  data_retention_days    = var.data_retention_days
  max_login_attempts     = var.max_login_attempts
  lockout_window_minutes = var.lockout_window_minutes
  trusted_proxies        = var.trusted_proxies
  default_from_email     = var.default_from_email
  vulntracker_base_url   = var.vulntracker_base_url
}

module "alb" {
  source = "../alb"

  app_name              = var.app_name
  environment           = var.environment
  vpc_id                = module.vpc.vpc_id
  public_subnet_ids     = module.vpc.public_subnet_ids
  alb_security_group_id = module.vpc.alb_security_group_id
  container_port        = var.container_port
  acm_certificate_arn   = var.alb_acm_certificate_arn
  health_check_path     = "/api/health/"
  access_logs_bucket    = var.alb_access_logs_bucket

  enable_ip_reputation_rules = var.enable_ip_reputation_rules
  enable_anonymous_ip_rules  = var.enable_anonymous_ip_rules
  enable_bot_control_rules   = var.enable_bot_control_rules
  enable_waf_logging         = var.enable_waf_logging
  kms_key_arn                = lookup(var.kms_key_arns, "s3", "")
}

module "ecs" {
  source = "../ecs"

  app_name              = var.app_name
  environment           = var.environment
  aws_region            = var.aws_region
  private_subnet_ids    = module.vpc.private_subnet_ids
  ecs_security_group_id = module.vpc.ecs_security_group_id
  target_group_arn      = module.alb.target_group_arn
  container_image       = var.container_image
  container_port        = var.container_port
  task_cpu              = var.ecs_task_cpu
  task_memory           = var.ecs_task_memory
  desired_count         = var.ecs_desired_count
  min_count             = var.ecs_min_count
  max_count             = var.ecs_max_count

  container_secrets    = module.secrets.container_secrets
  secrets_manager_arns = module.secrets.secrets_manager_arns
  ssm_parameter_arns   = module.secrets.ssm_parameter_arns

  log_group_kms_key_id    = lookup(var.kms_key_arns, "logs", var.log_group_kms_key_id)
  alb_arn_suffix          = module.alb.alb_arn_suffix
  target_group_arn_suffix = module.alb.target_group_arn_suffix
  alarm_sns_topic_arn     = var.sns_topic_arn
}

module "rds" {
  source = "../rds"

  app_name              = var.app_name
  environment           = var.environment
  is_primary            = var.is_primary
  source_db_arn         = var.rds_source_arn
  replica_kms_key_arn   = var.rds_replica_kms_key_arn
  private_subnet_ids    = module.vpc.private_subnet_ids
  rds_security_group_id = module.vpc.rds_security_group_id
  instance_class        = var.db_instance_class
  allocated_storage     = var.db_allocated_storage
  db_name               = var.db_name
  db_username           = var.db_username
  db_password           = var.db_password
  multi_az              = var.db_multi_az
  kms_key_arn           = lookup(var.kms_key_arns, "rds", "")
}

module "redis" {
  source = "../redis"

  app_name                    = var.app_name
  environment                 = var.environment
  is_primary                  = var.is_primary
  enable_global_datastore     = var.enable_global_datastore
  global_replication_group_id = var.redis_global_replication_group_id
  private_subnet_ids          = module.vpc.private_subnet_ids
  redis_security_group_id     = module.vpc.redis_security_group_id
  node_type                   = var.redis_node_type
  num_cache_nodes             = var.redis_num_cache_nodes
  snapshot_retention_limit    = var.redis_snapshot_retention_limit
  snapshot_window             = var.redis_snapshot_window
}

# Per-region S3 bucket for frontend assets (referenced by CDN origin groups)
resource "aws_s3_bucket" "frontend" {
  bucket = "${local.name_prefix}-frontend-${var.aws_region}"

  tags = {
    Name = "${local.name_prefix}-frontend-${var.aws_region}"
  }
}

resource "aws_s3_bucket_versioning" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = lookup(var.kms_key_arns, "s3", "") != "" ? "aws:kms" : "AES256"
      kms_master_key_id = lookup(var.kms_key_arns, "s3", "") != "" ? var.kms_key_arns["s3"] : null
    }
    bucket_key_enabled = lookup(var.kms_key_arns, "s3", "") != ""
  }
}

resource "aws_s3_bucket" "access_logs" {
  bucket = "${local.name_prefix}-access-logs-${var.aws_region}"

  tags = {
    Name = "${local.name_prefix}-access-logs-${var.aws_region}"
  }
}

resource "aws_s3_bucket_versioning" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = lookup(var.kms_key_arns, "s3", "") != "" ? "aws:kms" : "AES256"
      kms_master_key_id = lookup(var.kms_key_arns, "s3", "") != "" ? var.kms_key_arns["s3"] : null
    }
    bucket_key_enabled = lookup(var.kms_key_arns, "s3", "") != ""
  }
}

resource "aws_s3_bucket_public_access_block" "access_logs" {
  bucket = aws_s3_bucket.access_logs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_logging" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  target_bucket = aws_s3_bucket.access_logs.id
  target_prefix = "frontend-access/"
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront OAC bucket policy — grants read access to the CDN distribution
resource "aws_s3_bucket_policy" "frontend" {
  count  = var.cloudfront_distribution_arn != "" ? 1 : 0
  bucket = aws_s3_bucket.frontend.id
  policy = data.aws_iam_policy_document.frontend_bucket_policy[0].json
}

data "aws_iam_policy_document" "frontend_bucket_policy" {
  count = var.cloudfront_distribution_arn != "" ? 1 : 0

  statement {
    sid    = "AllowCloudFrontOAC"
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["cloudfront.amazonaws.com"]
    }

    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.frontend.arn}/*"]

    condition {
      test     = "StringEquals"
      variable = "AWS:SourceArn"
      values   = [var.cloudfront_distribution_arn]
    }
  }
}

# Cross-region replication from primary to secondary bucket
resource "aws_s3_bucket_replication_configuration" "frontend" {
  count  = var.is_primary && var.s3_replication_destination_bucket_arn != "" ? 1 : 0
  bucket = aws_s3_bucket.frontend.id
  role   = var.s3_replication_role_arn

  rule {
    id     = "replicate-frontend"
    status = "Enabled"

    destination {
      bucket        = var.s3_replication_destination_bucket_arn
      storage_class = "STANDARD"
    }
  }

  depends_on = [aws_s3_bucket_versioning.frontend]
}
