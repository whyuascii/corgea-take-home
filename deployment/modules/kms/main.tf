data "aws_caller_identity" "current" {}

locals {
  name_prefix = "${var.app_name}-${var.environment}"

  keys = {
    rds = {
      description = "Encrypt RDS storage at rest"
      service     = "rds.${var.aws_region}.amazonaws.com"
    }
    secrets = {
      description = "Encrypt Secrets Manager secrets"
      service     = "secretsmanager.${var.aws_region}.amazonaws.com"
    }
    s3 = {
      description = "Encrypt S3 bucket objects"
      service     = "s3.amazonaws.com"
    }
    logs = {
      description = "Encrypt CloudWatch Logs"
      service     = "logs.${var.aws_region}.amazonaws.com"
    }
    cloudtrail = {
      description = "Encrypt CloudTrail logs"
      service     = "cloudtrail.amazonaws.com"
    }
  }
}

resource "aws_kms_key" "main" {
  for_each = local.keys

  description             = "${local.name_prefix} — ${each.value.description}"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  rotation_period_in_days = 365

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "RootAccountFullAccess"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },
      {
        Sid    = "AllowServiceUsage"
        Effect = "Allow"
        Principal = {
          Service = each.value.service
        }
        Action = [
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:Encrypt",
          "kms:GenerateDataKey*",
          "kms:ReEncrypt*",
        ]
        Resource = "*"
      },
    ]
  })

  tags = {
    Name    = "${local.name_prefix}-${each.key}"
    Purpose = each.key
  }
}

resource "aws_kms_alias" "main" {
  for_each = local.keys

  name          = "alias/${local.name_prefix}-${each.key}"
  target_key_id = aws_kms_key.main[each.key].key_id
}
