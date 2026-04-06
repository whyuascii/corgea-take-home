locals {
  vulntracker_base_url = var.vulntracker_base_url != "" ? var.vulntracker_base_url : "https://${var.domain_name}"
}

module "kms" {
  source = "./modules/kms"

  providers = {
    aws = aws.primary
  }

  app_name    = var.app_name
  environment = var.environment
  aws_region  = var.primary_region
}

module "kms_secondary" {
  source = "./modules/kms"
  count  = var.enable_cross_region ? 1 : 0

  providers = {
    aws = aws.secondary
  }

  app_name    = var.app_name
  environment = var.environment
  aws_region  = var.secondary_region
}

module "security" {
  source = "./modules/security"

  providers = {
    aws = aws.primary
  }

  app_name    = var.app_name
  environment = var.environment
  aws_region  = var.primary_region

  enable_guardduty    = var.enable_guardduty
  enable_security_hub = var.enable_security_hub
  enable_cloudtrail   = var.enable_cloudtrail
  enable_aws_config   = var.enable_aws_config
  alert_email         = var.alert_email
  kms_key_arns        = module.kms.key_arns
}

# =============================================================================
# Primary Region
# =============================================================================

module "primary" {
  source = "./modules/region"

  providers = {
    aws = aws.primary
  }

  app_name    = var.app_name
  environment = var.environment
  aws_region  = var.primary_region
  is_primary  = true

  vpc_cidr             = var.primary_vpc_cidr
  availability_zones   = var.primary_availability_zones
  public_subnet_cidrs  = var.primary_public_subnet_cidrs
  private_subnet_cidrs = var.primary_private_subnet_cidrs
  single_nat_gateway   = var.primary_single_nat_gateway

  container_image   = var.container_image
  container_port    = var.container_port
  ecs_task_cpu      = var.ecs_task_cpu
  ecs_task_memory   = var.ecs_task_memory
  ecs_desired_count = var.ecs_desired_count
  ecs_min_count     = var.ecs_min_count
  ecs_max_count     = var.ecs_max_count

  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  db_name              = var.db_name
  db_username          = var.db_username
  db_password          = var.db_password
  db_multi_az          = var.db_multi_az

  redis_node_type                = var.redis_node_type
  redis_num_cache_nodes          = var.redis_num_cache_nodes
  redis_snapshot_retention_limit = var.redis_snapshot_retention_limit
  redis_snapshot_window          = var.redis_snapshot_window
  redis_auth_token               = var.redis_auth_token
  enable_global_datastore        = var.enable_cross_region && var.enable_global_datastore

  alb_acm_certificate_arn = var.primary_alb_acm_certificate_arn

  django_secret_key    = var.django_secret_key
  field_encryption_key = var.field_encryption_key
  resend_api_key       = var.resend_api_key
  sentry_dsn           = var.sentry_dsn
  jira_api_token       = var.jira_api_token
  linear_api_key       = var.linear_api_key

  django_allowed_hosts   = var.django_allowed_hosts
  cors_allowed_origins   = var.cors_allowed_origins
  data_retention_days    = var.data_retention_days
  max_login_attempts     = var.max_login_attempts
  lockout_window_minutes = var.lockout_window_minutes
  trusted_proxies        = var.trusted_proxies
  default_from_email     = var.default_from_email
  vulntracker_base_url   = local.vulntracker_base_url

  log_group_kms_key_id   = var.log_group_kms_key_id
  alb_access_logs_bucket = var.alb_access_logs_bucket

  kms_key_arns               = module.kms.key_arns
  enable_vpc_endpoints       = var.enable_vpc_endpoints
  enable_ip_reputation_rules = var.enable_ip_reputation_rules
  enable_anonymous_ip_rules  = var.enable_anonymous_ip_rules
  enable_bot_control_rules   = var.enable_bot_control_rules
  enable_waf_logging         = var.enable_waf_logging
  sns_topic_arn              = module.security.sns_topic_arn

  cloudfront_distribution_arn           = module.cdn.cloudfront_distribution_arn
  s3_replication_destination_bucket_arn = var.enable_cross_region ? module.secondary[0].frontend_bucket_arn : ""
  s3_replication_role_arn               = var.enable_cross_region ? aws_iam_role.s3_replication[0].arn : ""
}

# =============================================================================
# Secondary Region (cross-region failover)
# =============================================================================

module "secondary" {
  source = "./modules/region"
  count  = var.enable_cross_region ? 1 : 0

  providers = {
    aws = aws.secondary
  }

  app_name    = var.app_name
  environment = var.environment
  aws_region  = var.secondary_region
  is_primary  = false

  vpc_cidr             = var.secondary_vpc_cidr
  availability_zones   = var.secondary_availability_zones
  public_subnet_cidrs  = var.secondary_public_subnet_cidrs
  private_subnet_cidrs = var.secondary_private_subnet_cidrs
  single_nat_gateway   = var.secondary_single_nat_gateway

  container_image   = var.container_image
  container_port    = var.container_port
  ecs_task_cpu      = var.ecs_task_cpu
  ecs_task_memory   = var.ecs_task_memory
  ecs_desired_count = var.secondary_ecs_desired_count
  ecs_min_count     = var.secondary_ecs_min_count
  ecs_max_count     = var.secondary_ecs_max_count

  db_instance_class       = var.secondary_db_instance_class
  db_allocated_storage    = var.db_allocated_storage
  db_name                 = var.db_name
  db_username             = var.db_username
  db_password             = var.db_password
  db_multi_az             = false
  rds_source_arn          = module.primary.rds_instance_arn
  rds_replica_kms_key_arn = var.rds_replica_kms_key_arn

  redis_node_type                   = var.redis_node_type
  redis_num_cache_nodes             = var.redis_num_cache_nodes
  redis_snapshot_retention_limit    = var.redis_snapshot_retention_limit
  redis_snapshot_window             = var.redis_snapshot_window
  redis_auth_token                  = var.redis_auth_token
  enable_global_datastore           = var.enable_global_datastore
  redis_global_replication_group_id = module.primary.redis_global_replication_group_id

  alb_acm_certificate_arn = var.secondary_alb_acm_certificate_arn

  django_secret_key    = var.django_secret_key
  field_encryption_key = var.field_encryption_key
  resend_api_key       = var.resend_api_key
  sentry_dsn           = var.sentry_dsn
  jira_api_token       = var.jira_api_token
  linear_api_key       = var.linear_api_key

  django_allowed_hosts   = var.django_allowed_hosts
  cors_allowed_origins   = var.cors_allowed_origins
  data_retention_days    = var.data_retention_days
  max_login_attempts     = var.max_login_attempts
  lockout_window_minutes = var.lockout_window_minutes
  trusted_proxies        = var.trusted_proxies
  default_from_email     = var.default_from_email
  vulntracker_base_url   = local.vulntracker_base_url

  kms_key_arns               = module.kms_secondary[0].key_arns
  enable_vpc_endpoints       = var.enable_vpc_endpoints
  enable_ip_reputation_rules = var.enable_ip_reputation_rules
  enable_anonymous_ip_rules  = var.enable_anonymous_ip_rules
  enable_bot_control_rules   = var.enable_bot_control_rules
  enable_waf_logging         = var.enable_waf_logging
  sns_topic_arn              = module.security.sns_topic_arn

  cloudfront_distribution_arn = module.cdn.cloudfront_distribution_arn
}

# =============================================================================
# Global — CDN (CloudFront with origin failover)
# =============================================================================

module "cdn" {
  source = "./modules/cdn"

  app_name    = var.app_name
  environment = var.environment

  domain_name         = var.domain_name
  acm_certificate_arn = var.acm_certificate_arn

  primary_alb_dns_name       = module.primary.alb_dns_name
  primary_bucket_domain_name = module.primary.frontend_bucket_domain_name

  secondary_alb_dns_name       = var.enable_cross_region ? module.secondary[0].alb_dns_name : ""
  secondary_bucket_domain_name = var.enable_cross_region ? module.secondary[0].frontend_bucket_domain_name : ""
}

# =============================================================================
# Global — DNS (Route 53 failover routing)
# =============================================================================

module "dns" {
  source = "./modules/dns"
  count  = var.hosted_zone_id != "" ? 1 : 0

  app_name    = var.app_name
  environment = var.environment

  hosted_zone_id  = var.hosted_zone_id
  domain_name     = var.domain_name
  api_domain_name = var.api_domain_name

  primary_alb_dns_name = module.primary.alb_dns_name
  primary_alb_zone_id  = module.primary.alb_zone_id

  secondary_alb_dns_name = var.enable_cross_region ? module.secondary[0].alb_dns_name : ""
  secondary_alb_zone_id  = var.enable_cross_region ? module.secondary[0].alb_zone_id : ""

  cloudfront_domain_name = module.cdn.cloudfront_domain_name
}

# =============================================================================
# S3 Cross-Region Replication IAM
# =============================================================================

resource "aws_iam_role" "s3_replication" {
  count    = var.enable_cross_region ? 1 : 0
  provider = aws.primary

  name = "${var.app_name}-${var.environment}-s3-replication"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "s3.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.app_name}-${var.environment}-s3-replication"
  }
}

resource "aws_iam_role_policy" "s3_replication" {
  count    = var.enable_cross_region ? 1 : 0
  provider = aws.primary

  name = "${var.app_name}-${var.environment}-s3-replication"
  role = aws_iam_role.s3_replication[0].id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "SourceBucketAccess"
        Effect = "Allow"
        Action = [
          "s3:GetReplicationConfiguration",
          "s3:ListBucket",
        ]
        Resource = [module.primary.frontend_bucket_arn]
      },
      {
        Sid    = "SourceObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObjectVersionForReplication",
          "s3:GetObjectVersionAcl",
          "s3:GetObjectVersionTagging",
        ]
        Resource = ["${module.primary.frontend_bucket_arn}/*"]
      },
      {
        Sid    = "DestinationBucketAccess"
        Effect = "Allow"
        Action = [
          "s3:ReplicateObject",
          "s3:ReplicateDelete",
          "s3:ReplicateTags",
        ]
        Resource = ["${module.secondary[0].frontend_bucket_arn}/*"]
      },
    ]
  })
}
