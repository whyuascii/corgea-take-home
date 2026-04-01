resource "aws_guardduty_detector" "main" {
  count = var.enable_guardduty ? 1 : 0

  enable = true

  datasources {
    s3_logs {
      enable = true
    }
  }

  tags = {
    Name = "${local.name_prefix}-guardduty"
  }
}
