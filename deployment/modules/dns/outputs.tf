output "api_primary_fqdn" {
  description = "FQDN of the primary API record"
  value       = aws_route53_record.api_primary.fqdn
}

output "frontend_fqdn" {
  description = "FQDN of the frontend record"
  value       = aws_route53_record.frontend.fqdn
}

output "primary_health_check_id" {
  description = "Route 53 health check ID for the primary ALB"
  value       = aws_route53_health_check.primary.id
}

output "secondary_health_check_id" {
  description = "Route 53 health check ID for the secondary ALB"
  value       = local.has_failover ? aws_route53_health_check.secondary[0].id : ""
}
