output "cluster_id" {
  description = "ECS cluster ID"
  value       = aws_ecs_cluster.main.id
}

output "cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "service_id" {
  description = "ECS service ID"
  value       = aws_ecs_service.backend.id
}

output "service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.backend.name
}

output "task_definition_arn" {
  description = "Task definition ARN"
  value       = aws_ecs_task_definition.backend.arn
}

output "task_execution_role_arn" {
  description = "Task execution IAM role ARN"
  value       = aws_iam_role.task_execution.arn
}

output "task_role_arn" {
  description = "Task IAM role ARN"
  value       = aws_iam_role.task.arn
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.ecs.name
}
