environment         = "prod"
enable_cross_region = true

# Primary region — us-east-1
primary_region               = "us-east-1"
primary_vpc_cidr             = "10.2.0.0/16"
primary_availability_zones   = ["us-east-1a", "us-east-1b", "us-east-1c"]
primary_public_subnet_cidrs  = ["10.2.1.0/24", "10.2.2.0/24", "10.2.3.0/24"]
primary_private_subnet_cidrs = ["10.2.10.0/24", "10.2.11.0/24", "10.2.12.0/24"]
primary_single_nat_gateway   = false

# Secondary region — us-west-2
secondary_region               = "us-west-2"
secondary_vpc_cidr             = "10.12.0.0/16"
secondary_availability_zones   = ["us-west-2a", "us-west-2b"]
secondary_public_subnet_cidrs  = ["10.12.1.0/24", "10.12.2.0/24"]
secondary_private_subnet_cidrs = ["10.12.10.0/24", "10.12.11.0/24"]
secondary_single_nat_gateway   = true

# ECS — primary
container_image   = "123456789012.dkr.ecr.us-east-1.amazonaws.com/vulntracker:v1.0.0"
ecs_task_cpu      = 1024
ecs_task_memory   = 2048
ecs_desired_count = 3
ecs_min_count     = 2
ecs_max_count     = 10

# ECS — secondary (warm standby)
secondary_ecs_desired_count = 1
secondary_ecs_min_count     = 1
secondary_ecs_max_count     = 6

# RDS — primary
db_instance_class    = "db.r6g.large"
db_allocated_storage = 100
db_name              = "vulntracker"
db_multi_az          = true

# RDS — secondary replica
secondary_db_instance_class = "db.r6g.large"

# Redis
redis_node_type                = "cache.r6g.large"
redis_num_cache_nodes          = 2
redis_snapshot_retention_limit = 7
enable_global_datastore        = true

# DNS / TLS
domain_name                       = "vulntracker.corgea.com"
api_domain_name                   = "api.vulntracker.corgea.com"
acm_certificate_arn               = "arn:aws:acm:us-east-1:123456789012:certificate/placeholder-prod-cert"
primary_alb_acm_certificate_arn   = "arn:aws:acm:us-east-1:123456789012:certificate/placeholder-prod-alb-cert"
secondary_alb_acm_certificate_arn = "arn:aws:acm:us-west-2:123456789012:certificate/placeholder-prod-alb-cert-west"

# App config
django_allowed_hosts   = "api.vulntracker.corgea.com"
cors_allowed_origins   = "https://vulntracker.corgea.com"
data_retention_days    = 365
max_login_attempts     = 5
lockout_window_minutes = 15
default_from_email     = "noreply@vulntracker.corgea.com"
vulntracker_base_url   = "https://vulntracker.corgea.com"

# Security
enable_guardduty           = true
enable_security_hub        = true
enable_cloudtrail          = true
enable_aws_config          = true
enable_vpc_endpoints       = true
enable_ip_reputation_rules = true
enable_anonymous_ip_rules  = true
enable_bot_control_rules   = true
enable_waf_logging         = true
alert_email                = "security@vulntracker.corgea.com"

# Secrets: pass via TF_VAR_django_secret_key, TF_VAR_field_encryption_key, etc.
