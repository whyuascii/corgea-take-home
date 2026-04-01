output "endpoint" {
  description = "Redis primary endpoint address"
  value       = aws_elasticache_replication_group.main.primary_endpoint_address
}

output "port" {
  description = "Redis port"
  value       = var.port
}

output "replication_group_id" {
  description = "ElastiCache replication group ID"
  value       = aws_elasticache_replication_group.main.id
}

output "global_replication_group_id" {
  description = "Global replication group ID (only set for primary with global datastore enabled)"
  value       = var.is_primary && var.enable_global_datastore ? aws_elasticache_global_replication_group.main[0].id : ""
}
