output "alb_dns_name" {
  description = "ALB DNS name"
  value       = module.alb.alb_dns_name
}

output "alb_zone_id" {
  description = "ALB Route53 zone ID"
  value       = module.alb.alb_zone_id
}

output "alb_arn" {
  description = "ALB ARN"
  value       = module.alb.alb_arn
}

output "rds_instance_arn" {
  description = "RDS instance ARN for cross-region replica linking"
  value       = module.rds.instance_arn
}

output "rds_endpoint" {
  description = "RDS endpoint hostname"
  value       = module.rds.endpoint
}

output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = module.redis.endpoint
}

output "redis_global_replication_group_id" {
  description = "Redis Global Datastore ID (primary only)"
  value       = module.redis.global_replication_group_id
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = module.ecs.cluster_name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = module.ecs.service_name
}

output "frontend_bucket_name" {
  description = "S3 frontend bucket name"
  value       = aws_s3_bucket.frontend.id
}

output "frontend_bucket_arn" {
  description = "S3 frontend bucket ARN"
  value       = aws_s3_bucket.frontend.arn
}

output "frontend_bucket_domain_name" {
  description = "S3 frontend bucket regional domain name"
  value       = aws_s3_bucket.frontend.bucket_regional_domain_name
}

output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "task_execution_role_arn" {
  description = "ECS task execution IAM role ARN"
  value       = module.ecs.task_execution_role_arn
}

output "task_role_arn" {
  description = "ECS task IAM role ARN"
  value       = module.ecs.task_role_arn
}
