locals {
  name_prefix = "${var.app_name}-${var.environment}"
}

resource "aws_elasticache_subnet_group" "main" {
  name       = "${local.name_prefix}-redis-subnet"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${local.name_prefix}-redis-subnet"
  }
}

resource "aws_elasticache_parameter_group" "redis7" {
  name   = "${local.name_prefix}-redis7-params"
  family = "redis7"

  parameter {
    name  = "maxmemory-policy"
    value = "allkeys-lru"
  }

  tags = {
    Name = "${local.name_prefix}-redis7-params"
  }
}

# Primary region creates the global replication group for cross-region failover
resource "aws_elasticache_global_replication_group" "main" {
  count = var.is_primary && var.enable_global_datastore ? 1 : 0

  global_replication_group_id_suffix   = "${var.app_name}-${var.environment}"
  primary_replication_group_id         = aws_elasticache_replication_group.main.id
  global_replication_group_description = "Global datastore for ${local.name_prefix}"
}

resource "aws_elasticache_replication_group" "main" {
  replication_group_id = "${local.name_prefix}-redis"
  description          = "Redis for ${local.name_prefix}"
  engine_version       = var.is_primary ? var.engine_version : null
  node_type            = var.is_primary || !var.enable_global_datastore ? var.node_type : null
  num_cache_clusters   = var.num_cache_nodes
  port                 = var.port
  parameter_group_name = aws_elasticache_parameter_group.redis7.name
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [var.redis_security_group_id]

  # Secondary region joins existing global datastore
  global_replication_group_id = !var.is_primary && var.enable_global_datastore ? var.global_replication_group_id : null

  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  auth_token                 = var.auth_token != "" ? var.auth_token : null
  automatic_failover_enabled = var.num_cache_nodes >= 2 ? var.automatic_failover_enabled : false

  snapshot_retention_limit = var.snapshot_retention_limit
  snapshot_window          = var.snapshot_retention_limit > 0 ? var.snapshot_window : null
  maintenance_window       = var.maintenance_window

  auto_minor_version_upgrade = true

  tags = {
    Name = "${local.name_prefix}-redis"
  }
}
