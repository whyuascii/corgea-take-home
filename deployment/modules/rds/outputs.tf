output "endpoint" {
  description = "RDS endpoint hostname"
  value       = var.is_primary ? aws_db_instance.primary[0].address : aws_db_instance.replica[0].address
}

output "port" {
  description = "RDS port"
  value       = var.is_primary ? aws_db_instance.primary[0].port : aws_db_instance.replica[0].port
}

output "db_name" {
  description = "Database name"
  value       = var.is_primary ? aws_db_instance.primary[0].db_name : ""
}

output "instance_id" {
  description = "RDS instance identifier"
  value       = var.is_primary ? aws_db_instance.primary[0].id : aws_db_instance.replica[0].id
}

output "instance_arn" {
  description = "RDS instance ARN"
  value       = var.is_primary ? aws_db_instance.primary[0].arn : aws_db_instance.replica[0].arn
}

output "password" {
  description = "Effective database password"
  value       = local.db_password
  sensitive   = true
}
