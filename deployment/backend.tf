terraform {
  backend "s3" {
    bucket         = "vulntracker-terraform-state"
    key            = "vulntracker/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "vulntracker-terraform-locks"
    encrypt        = true
    kms_key_id     = "alias/vulntracker-terraform-state"
  }
}
