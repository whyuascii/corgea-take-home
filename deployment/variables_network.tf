# --- Primary Region ---

variable "primary_region" {
  description = "AWS region for the primary stack"
  type        = string
  default     = "us-east-1"
}

variable "primary_vpc_cidr" {
  description = "CIDR block for the primary VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "primary_availability_zones" {
  description = "Availability zones for the primary region"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "primary_public_subnet_cidrs" {
  description = "Public subnet CIDRs for the primary region"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "primary_private_subnet_cidrs" {
  description = "Private subnet CIDRs for the primary region"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "primary_single_nat_gateway" {
  description = "Use a single NAT Gateway in the primary region"
  type        = bool
  default     = true
}

# --- Secondary Region ---

variable "secondary_region" {
  description = "AWS region for the secondary/failover stack"
  type        = string
  default     = "us-west-2"
}

variable "secondary_vpc_cidr" {
  description = "CIDR block for the secondary VPC"
  type        = string
  default     = "10.10.0.0/16"
}

variable "secondary_availability_zones" {
  description = "Availability zones for the secondary region"
  type        = list(string)
  default     = ["us-west-2a", "us-west-2b"]
}

variable "secondary_public_subnet_cidrs" {
  description = "Public subnet CIDRs for the secondary region"
  type        = list(string)
  default     = ["10.10.1.0/24", "10.10.2.0/24"]
}

variable "secondary_private_subnet_cidrs" {
  description = "Private subnet CIDRs for the secondary region"
  type        = list(string)
  default     = ["10.10.10.0/24", "10.10.11.0/24"]
}

variable "secondary_single_nat_gateway" {
  description = "Use a single NAT Gateway in the secondary region"
  type        = bool
  default     = true
}
