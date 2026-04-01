environment         = "staging"
enable_cross_region = false

# Primary region
primary_region               = "us-east-1"
primary_vpc_cidr             = "10.1.0.0/16"
primary_availability_zones   = ["us-east-1a", "us-east-1b"]
primary_public_subnet_cidrs  = ["10.1.1.0/24", "10.1.2.0/24"]
primary_private_subnet_cidrs = ["10.1.10.0/24", "10.1.11.0/24"]
primary_single_nat_gateway   = true

# ECS
container_image   = "123456789012.dkr.ecr.us-east-1.amazonaws.com/vulntracker:staging"
ecs_task_cpu      = 512
ecs_task_memory   = 1024
ecs_desired_count = 2
ecs_min_count     = 1
ecs_max_count     = 4

# RDS
db_instance_class    = "db.t3.small"
db_allocated_storage = 50
db_name              = "vulntracker_staging"
db_multi_az          = false

# Redis
redis_node_type                = "cache.t3.small"
redis_num_cache_nodes          = 1
redis_snapshot_retention_limit = 3

# DNS / TLS
domain_name                     = "staging.vulntracker.corgea.com"
api_domain_name                 = "api.staging.vulntracker.corgea.com"
acm_certificate_arn             = "arn:aws:acm:us-east-1:123456789012:certificate/placeholder-staging-cert"
primary_alb_acm_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/placeholder-staging-alb-cert"

# App config
django_allowed_hosts   = "api.staging.vulntracker.corgea.com"
cors_allowed_origins   = "https://staging.vulntracker.corgea.com"
data_retention_days    = 60
max_login_attempts     = 5
lockout_window_minutes = 15
default_from_email     = "noreply@staging.vulntracker.corgea.com"
vulntracker_base_url   = "https://staging.vulntracker.corgea.com"

# Security
enable_guardduty           = true
enable_security_hub        = true
enable_cloudtrail          = true
enable_aws_config          = true
enable_vpc_endpoints       = true
enable_ip_reputation_rules = true
enable_anonymous_ip_rules  = true
enable_bot_control_rules   = false
enable_waf_logging         = true
alert_email                = "security-staging@vulntracker.corgea.com"

# Secrets: pass via TF_VAR_django_secret_key, TF_VAR_field_encryption_key, etc.
