variable "app_name" {
  description = "Application name"
  type        = string
}

variable "environment" {
  description = "Deployment environment"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
}

variable "container_port" {
  description = "Port the backend container listens on"
  type        = number
  default     = 8000
}

variable "single_nat_gateway" {
  description = "Use a single NAT Gateway instead of one per AZ"
  type        = bool
  default     = true
}

variable "log_group_kms_key_id" {
  description = "KMS key ARN for encrypting CloudWatch log groups"
  type        = string
  default     = ""
}

variable "enable_vpc_endpoints" {
  description = "Create VPC endpoints for AWS services (S3, ECR, Secrets Manager, etc.)"
  type        = bool
  default     = true
}

variable "aws_region" {
  description = "AWS region for VPC endpoint service names"
  type        = string
}
