output "container_secrets" {
  description = "Map of env var name to secret/parameter ARN for ECS task definition"
  value = merge(
    { for k, v in aws_secretsmanager_secret.main : k => v.arn },
    { for k, v in aws_ssm_parameter.main : k => v.arn }
  )
}

output "secrets_manager_arns" {
  description = "All Secrets Manager secret ARNs for IAM policy"
  value       = [for s in aws_secretsmanager_secret.main : s.arn]
}

output "ssm_parameter_arns" {
  description = "All SSM Parameter Store ARNs for IAM policy"
  value       = [for p in aws_ssm_parameter.main : p.arn]
}
