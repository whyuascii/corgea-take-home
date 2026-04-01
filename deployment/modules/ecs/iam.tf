data "aws_iam_policy_document" "ecs_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "task_execution" {
  name               = "${local.name_prefix}-task-exec-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Name = "${local.name_prefix}-task-exec-role"
  }
}

resource "aws_iam_role_policy_attachment" "task_execution_base" {
  role       = aws_iam_role.task_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

data "aws_iam_policy_document" "ssm_read" {
  statement {
    sid       = "ReadSSMParameters"
    effect    = "Allow"
    actions   = ["ssm:GetParameters", "ssm:GetParameter"]
    resources = var.ssm_parameter_arns
  }
}

resource "aws_iam_role_policy" "task_execution_ssm" {
  name   = "${local.name_prefix}-ssm-read"
  role   = aws_iam_role.task_execution.id
  policy = data.aws_iam_policy_document.ssm_read.json
}

data "aws_iam_policy_document" "secrets_manager_read" {
  statement {
    sid       = "ReadSecretsManager"
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = var.secrets_manager_arns
  }
}

resource "aws_iam_role_policy" "task_execution_secrets_manager" {
  name   = "${local.name_prefix}-secrets-manager-read"
  role   = aws_iam_role.task_execution.id
  policy = data.aws_iam_policy_document.secrets_manager_read.json
}

resource "aws_iam_role" "task" {
  name               = "${local.name_prefix}-task-role"
  assume_role_policy = data.aws_iam_policy_document.ecs_assume_role.json

  tags = {
    Name = "${local.name_prefix}-task-role"
  }
}

data "aws_iam_policy_document" "task_runtime" {
  statement {
    sid    = "CloudWatchLogs"
    effect = "Allow"
    actions = [
      "logs:CreateLogStream",
      "logs:PutLogEvents",
    ]
    resources = ["${aws_cloudwatch_log_group.ecs.arn}:*"]
  }

  statement {
    sid    = "SSMAtRuntime"
    effect = "Allow"
    actions = [
      "ssm:GetParameters",
      "ssm:GetParameter",
      "ssm:GetParametersByPath",
    ]
    resources = var.ssm_parameter_arns
  }

  statement {
    sid       = "SecretsManagerAtRuntime"
    effect    = "Allow"
    actions   = ["secretsmanager:GetSecretValue"]
    resources = var.secrets_manager_arns
  }
}

resource "aws_iam_role_policy" "task_runtime" {
  name   = "${local.name_prefix}-task-runtime"
  role   = aws_iam_role.task.id
  policy = data.aws_iam_policy_document.task_runtime.json
}
