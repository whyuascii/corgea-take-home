variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "private_subnet_ids" {
  description = "Private subnet IDs for ECS tasks"
  type        = list(string)
}

variable "ecs_security_group_id" {
  description = "Security group ID for ECS tasks"
  type        = string
}

variable "target_group_arn" {
  description = "ALB target group ARN"
  type        = string
}

variable "container_image" {
  description = "Docker image URI for the backend container"
  type        = string
}

variable "container_port" {
  description = "Port the container listens on"
  type        = number
  default     = 8000
}

variable "task_cpu" {
  description = "CPU units for the task (1 vCPU = 1024)"
  type        = number
  default     = 512
}

variable "task_memory" {
  description = "Memory in MiB for the task"
  type        = number
  default     = 1024
}

variable "desired_count" {
  description = "Desired number of running tasks"
  type        = number
  default     = 2
}

variable "min_count" {
  description = "Minimum tasks for autoscaling"
  type        = number
  default     = 1
}

variable "max_count" {
  description = "Maximum tasks for autoscaling"
  type        = number
  default     = 4
}

variable "cpu_target_value" {
  description = "Target CPU utilization % for autoscaling"
  type        = number
  default     = 70
}

variable "memory_target_value" {
  description = "Target memory utilization % for autoscaling"
  type        = number
  default     = 80
}

variable "container_secrets" {
  description = "Map of environment variable name to Secrets Manager or SSM Parameter ARN"
  type        = map(string)
}

variable "secrets_manager_arns" {
  description = "Aggregate Secrets Manager ARNs for IAM policy"
  type        = list(string)
}

variable "ssm_parameter_arns" {
  description = "Aggregate SSM Parameter Store ARNs for IAM policy"
  type        = list(string)
}

variable "log_group_kms_key_id" {
  description = "KMS key ARN for CloudWatch log encryption"
  type        = string
  default     = ""
}

variable "alarm_sns_topic_arn" {
  description = "SNS topic ARN for CloudWatch alarm notifications"
  type        = string
  default     = ""
}

variable "alarm_cpu_threshold" {
  description = "CPU utilization threshold % for alarm"
  type        = number
  default     = 85
}

variable "alarm_memory_threshold" {
  description = "Memory utilization threshold % for alarm"
  type        = number
  default     = 85
}

variable "alarm_alb_5xx_threshold" {
  description = "ALB 5xx error count threshold for alarm"
  type        = number
  default     = 50
}

variable "alb_arn_suffix" {
  description = "ALB ARN suffix for CloudWatch dimensions"
  type        = string
  default     = ""
}

variable "target_group_arn_suffix" {
  description = "Target group ARN suffix for CloudWatch dimensions"
  type        = string
  default     = ""
}
