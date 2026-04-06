resource "aws_guardduty_detector" "main" {
  count = var.enable_guardduty ? 1 : 0

  enable = true

  datasources {
    s3_logs {
      enable = true
    }

    malware_protection {
      scan_ec2_instance_with_findings {
        ebs_volumes {
          enable = true
        }
      }
    }

    kubernetes {
      audit_logs {
        enable = false
      }
    }
  }

  tags = {
    Name = "${local.name_prefix}-guardduty"
  }
}
