variable "container_image" {
  description = "Docker image URI for the backend container"
  type        = string
  default     = "123456789012.dkr.ecr.us-east-1.amazonaws.com/vulntracker:v1.0.0"

  validation {
    condition     = !can(regex(":latest$", var.container_image))
    error_message = "Container image must not use the 'latest' tag."
  }
}

variable "container_port" {
  description = "Port the backend container listens on"
  type        = number
  default     = 8000
}

variable "ecs_task_cpu" {
  description = "CPU units for the ECS task (1 vCPU = 1024)"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory in MiB for the ECS task"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_min_count" {
  description = "Minimum ECS tasks for autoscaling"
  type        = number
  default     = 1
}

variable "ecs_max_count" {
  description = "Maximum ECS tasks for autoscaling"
  type        = number
  default     = 4
}

# Secondary region can run a smaller fleet
variable "secondary_ecs_desired_count" {
  description = "Desired ECS tasks in the secondary region"
  type        = number
  default     = 1
}

variable "secondary_ecs_min_count" {
  description = "Minimum ECS tasks in the secondary region"
  type        = number
  default     = 1
}

variable "secondary_ecs_max_count" {
  description = "Maximum ECS tasks in the secondary region"
  type        = number
  default     = 4
}
