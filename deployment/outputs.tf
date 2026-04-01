# --- Primary Region ---

output "primary_vpc_id" {
  description = "Primary region VPC ID"
  value       = module.primary.vpc_id
}

output "primary_alb_dns_name" {
  description = "Primary region ALB DNS name"
  value       = module.primary.alb_dns_name
}

output "primary_ecs_cluster_name" {
  description = "Primary region ECS cluster name"
  value       = module.primary.ecs_cluster_name
}

output "primary_ecs_service_name" {
  description = "Primary region ECS service name"
  value       = module.primary.ecs_service_name
}

output "primary_rds_endpoint" {
  description = "Primary region RDS endpoint"
  value       = module.primary.rds_endpoint
  sensitive   = true
}

output "primary_redis_endpoint" {
  description = "Primary region Redis endpoint"
  value       = module.primary.redis_endpoint
  sensitive   = true
}

output "primary_frontend_bucket" {
  description = "Primary region S3 frontend bucket name"
  value       = module.primary.frontend_bucket_name
}

# --- Secondary Region ---

output "secondary_vpc_id" {
  description = "Secondary region VPC ID"
  value       = var.enable_cross_region ? module.secondary[0].vpc_id : ""
}

output "secondary_alb_dns_name" {
  description = "Secondary region ALB DNS name"
  value       = var.enable_cross_region ? module.secondary[0].alb_dns_name : ""
}

output "secondary_ecs_cluster_name" {
  description = "Secondary region ECS cluster name"
  value       = var.enable_cross_region ? module.secondary[0].ecs_cluster_name : ""
}

output "secondary_ecs_service_name" {
  description = "Secondary region ECS service name"
  value       = var.enable_cross_region ? module.secondary[0].ecs_service_name : ""
}

output "secondary_rds_endpoint" {
  description = "Secondary region RDS endpoint"
  value       = var.enable_cross_region ? module.secondary[0].rds_endpoint : ""
  sensitive   = true
}

output "secondary_frontend_bucket" {
  description = "Secondary region S3 frontend bucket name"
  value       = var.enable_cross_region ? module.secondary[0].frontend_bucket_name : ""
}

# --- Global ---

output "cloudfront_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.cdn.cloudfront_domain_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID (for cache invalidation)"
  value       = module.cdn.cloudfront_distribution_id
}

output "cross_region_enabled" {
  description = "Whether cross-region failover is active"
  value       = var.enable_cross_region
}
