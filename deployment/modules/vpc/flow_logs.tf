resource "aws_cloudwatch_log_group" "flow_logs" {
  name              = "/vpc/${local.name_prefix}-flow-logs"
  retention_in_days = 90
  kms_key_id        = var.log_group_kms_key_id != "" ? var.log_group_kms_key_id : null

  tags = {
    Name = "${local.name_prefix}-flow-logs"
  }
}

data "aws_iam_policy_document" "flow_logs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["vpc-flow-logs.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "flow_logs" {
  name               = "${local.name_prefix}-flow-logs-role"
  assume_role_policy = data.aws_iam_policy_document.flow_logs_assume_role.json

  tags = {
    Name = "${local.name_prefix}-flow-logs-role"
  }
}

data "aws_iam_policy_document" "flow_logs_policy" {
  statement {
    sid    = "AllowFlowLogWrites"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
      "logs:DescribeLogStreams",
    ]
    resources = ["${aws_cloudwatch_log_group.flow_logs.arn}:*"]
  }
}

resource "aws_iam_role_policy" "flow_logs" {
  name   = "${local.name_prefix}-flow-logs-policy"
  role   = aws_iam_role.flow_logs.id
  policy = data.aws_iam_policy_document.flow_logs_policy.json
}

resource "aws_flow_log" "main" {
  vpc_id               = aws_vpc.main.id
  traffic_type         = "ALL"
  log_destination      = aws_cloudwatch_log_group.flow_logs.arn
  log_destination_type = "cloud-watch-logs"
  iam_role_arn         = aws_iam_role.flow_logs.arn

  tags = {
    Name = "${local.name_prefix}-flow-log"
  }
}
