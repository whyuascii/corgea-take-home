environment         = "dev"
enable_cross_region = false

# Primary region
primary_region               = "us-east-1"
primary_vpc_cidr             = "10.0.0.0/16"
primary_availability_zones   = ["us-east-1a", "us-east-1b"]
primary_public_subnet_cidrs  = ["10.0.1.0/24", "10.0.2.0/24"]
primary_private_subnet_cidrs = ["10.0.10.0/24", "10.0.11.0/24"]
primary_single_nat_gateway   = true

# ECS
container_image   = "123456789012.dkr.ecr.us-east-1.amazonaws.com/vulntracker:dev"
ecs_task_cpu      = 256
ecs_task_memory   = 512
ecs_desired_count = 1
ecs_min_count     = 1
ecs_max_count     = 2

# RDS
db_instance_class    = "db.t3.micro"
db_allocated_storage = 20
db_name              = "vulntracker_dev"
db_multi_az          = false

# Redis
redis_node_type                = "cache.t3.micro"
redis_num_cache_nodes          = 1
redis_snapshot_retention_limit = 1

# DNS / TLS
domain_name                     = "dev.vulntracker.corgea.com"
api_domain_name                 = "api.dev.vulntracker.corgea.com"
acm_certificate_arn             = "arn:aws:acm:us-east-1:123456789012:certificate/placeholder-dev-cert"
primary_alb_acm_certificate_arn = "arn:aws:acm:us-east-1:123456789012:certificate/placeholder-dev-alb-cert"

# App config
django_allowed_hosts   = "api.dev.vulntracker.corgea.com,localhost"
cors_allowed_origins   = "https://dev.vulntracker.corgea.com,http://localhost:5173"
data_retention_days    = 30
max_login_attempts     = 5
lockout_window_minutes = 15
default_from_email     = "noreply@dev.vulntracker.corgea.com"
vulntracker_base_url   = "https://dev.vulntracker.corgea.com"

# Security
enable_guardduty           = false
enable_security_hub        = false
enable_cloudtrail          = false
enable_aws_config          = false
enable_vpc_endpoints       = true
enable_ip_reputation_rules = false
enable_anonymous_ip_rules  = false
enable_bot_control_rules   = false
enable_waf_logging         = false
alert_email                = ""

# Secrets: pass via TF_VAR_django_secret_key, TF_VAR_field_encryption_key, etc.
