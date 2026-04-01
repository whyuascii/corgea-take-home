locals {
  ssm_prefix     = "/${var.app_name}/${var.environment}"
  secrets_prefix = "${var.app_name}/${var.environment}"

  common_tags = {
    Application = var.app_name
    Environment = var.environment
  }

  secrets = {
    DJANGO_SECRET_KEY    = { value = var.django_secret_key, required = true }
    FIELD_ENCRYPTION_KEY = { value = var.field_encryption_key, required = true }
    POSTGRES_PASSWORD    = { value = var.postgres_password, required = true }
    DATABASE_URL         = { value = var.database_url, required = true }
    REDIS_URL            = { value = var.redis_url, required = true }
    RESEND_API_KEY       = { value = var.resend_api_key, required = false }
    SENTRY_DSN           = { value = var.sentry_dsn, required = false }
    JIRA_API_TOKEN       = { value = var.jira_api_token, required = false }
    LINEAR_API_KEY       = { value = var.linear_api_key, required = false }
  }

  ssm_params = {
    DJANGO_ALLOWED_HOSTS   = var.allowed_hosts
    CORS_ALLOWED_ORIGINS   = var.cors_allowed_origins
    DATA_RETENTION_DAYS    = tostring(var.data_retention_days)
    MAX_LOGIN_ATTEMPTS     = tostring(var.max_login_attempts)
    LOCKOUT_WINDOW_MINUTES = tostring(var.lockout_window_minutes)
    TRUSTED_PROXIES        = var.trusted_proxies
    DEFAULT_FROM_EMAIL     = var.default_from_email
    VULNTRACKER_BASE_URL   = var.vulntracker_base_url
  }
}

resource "aws_secretsmanager_secret" "main" {
  for_each = local.secrets

  name                    = "${local.secrets_prefix}/${each.key}"
  description             = "${replace(each.key, "_", " ")} for ${var.app_name} ${var.environment}"
  recovery_window_in_days = var.environment == "prod" ? 30 : 7
  kms_key_id              = var.kms_key_id != "" ? var.kms_key_id : null

  tags = merge(local.common_tags, {
    Name = "${var.app_name}-${var.environment}-${lower(replace(each.key, "_", "-"))}"
  })
}

resource "aws_secretsmanager_secret_version" "main" {
  for_each = local.secrets

  secret_id     = aws_secretsmanager_secret.main[each.key].id
  secret_string = each.value.required ? each.value.value : (each.value.value != "" ? each.value.value : "placeholder")
}

resource "aws_ssm_parameter" "main" {
  for_each = local.ssm_params

  name        = "${local.ssm_prefix}/${each.key}"
  description = "${replace(each.key, "_", " ")} for ${var.app_name} ${var.environment}"
  type        = "String"
  value       = each.value

  tags = merge(local.common_tags, {
    Name = "${var.app_name}-${var.environment}-${lower(replace(each.key, "_", "-"))}"
  })
}
