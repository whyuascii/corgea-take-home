# Generated for password reset + login attempt tracking

import accounts.models
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PasswordResetToken",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "token",
                    models.CharField(
                        default=accounts.models._default_token,
                        max_length=128,
                        unique=True,
                    ),
                ),
                ("expires_at", models.DateTimeField(default=accounts.models._default_expiry)),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="password_reset_tokens",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="LoginAttempt",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("username", models.CharField(max_length=150)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("success", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="passwordresettoken",
            index=models.Index(fields=["token"], name="accounts_pa_token_affdf2_idx"),
        ),
        migrations.AddIndex(
            model_name="passwordresettoken",
            index=models.Index(
                fields=["user", "-created_at"], name="accounts_pa_user_id_13d348_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="loginattempt",
            index=models.Index(
                fields=["username", "-created_at"], name="accounts_lo_usernam_ccc69c_idx"
            ),
        ),
        migrations.AddIndex(
            model_name="loginattempt",
            index=models.Index(
                fields=["ip_address", "-created_at"], name="accounts_lo_ip_addr_a49186_idx"
            ),
        ),
    ]
