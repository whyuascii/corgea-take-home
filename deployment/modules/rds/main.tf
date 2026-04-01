locals {
  name_prefix = "${var.app_name}-${var.environment}"
  db_password = var.is_primary ? (var.db_password != "" ? var.db_password : random_password.db_password[0].result) : ""
}

resource "random_password" "db_password" {
  count            = var.is_primary ? 1 : 0
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet-group"
  subnet_ids = var.private_subnet_ids

  tags = {
    Name = "${local.name_prefix}-db-subnet-group"
  }
}

resource "aws_db_parameter_group" "postgres16" {
  name   = "${local.name_prefix}-pg16-params"
  family = "postgres16"

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name         = "shared_preload_libraries"
    value        = "pg_stat_statements"
    apply_method = "pending-reboot"
  }

  parameter {
    name  = "pg_stat_statements.track"
    value = "all"
  }

  tags = {
    Name = "${local.name_prefix}-pg16-params"
  }

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_db_instance" "primary" {
  count = var.is_primary ? 1 : 0

  identifier = "${local.name_prefix}-postgres"

  engine         = "postgres"
  engine_version = "16"
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = var.kms_key_arn != "" ? var.kms_key_arn : null

  db_name  = var.db_name
  username = var.db_username
  password = local.db_password

  multi_az                            = var.multi_az
  db_subnet_group_name                = aws_db_subnet_group.main.name
  vpc_security_group_ids              = [var.rds_security_group_id]
  parameter_group_name                = aws_db_parameter_group.postgres16.name
  publicly_accessible                 = false
  iam_database_authentication_enabled = true

  backup_retention_period = var.environment == "prod" ? 35 : var.backup_retention_period
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  deletion_protection       = true
  skip_final_snapshot       = var.environment == "prod" ? false : var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${local.name_prefix}-final-snapshot"

  performance_insights_enabled    = var.performance_insights_enabled
  performance_insights_kms_key_id = var.kms_key_arn != "" ? var.kms_key_arn : null
  monitoring_interval             = var.environment == "prod" ? 60 : 0

  auto_minor_version_upgrade = true
  copy_tags_to_snapshot      = true

  tags = {
    Name = "${local.name_prefix}-postgres"
  }
}

# Cross-region read replica — promoted manually during failover
resource "aws_db_instance" "replica" {
  count = var.is_primary ? 0 : 1

  identifier          = "${local.name_prefix}-postgres-replica"
  replicate_source_db = var.source_db_arn
  instance_class      = var.instance_class

  storage_type      = "gp3"
  storage_encrypted = true
  kms_key_id        = var.replica_kms_key_arn

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.rds_security_group_id]
  parameter_group_name   = aws_db_parameter_group.postgres16.name
  publicly_accessible    = false

  backup_retention_period = var.backup_retention_period
  backup_window           = "03:00-04:00"
  maintenance_window      = "sun:04:00-sun:05:00"

  deletion_protection = var.deletion_protection
  skip_final_snapshot = true

  performance_insights_enabled = var.performance_insights_enabled
  monitoring_interval          = var.environment == "prod" ? 60 : 0

  auto_minor_version_upgrade = true

  tags = {
    Name = "${local.name_prefix}-postgres-replica"
  }
}
