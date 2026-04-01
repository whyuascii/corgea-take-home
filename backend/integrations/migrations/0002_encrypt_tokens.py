import base64
import hashlib

from django.conf import settings
from django.db import migrations

import core.fields


def encrypt_existing_tokens(apps, schema_editor):
    """Encrypt existing plain-text integration tokens using Fernet."""
    from cryptography.fernet import Fernet

    key = settings.FIELD_ENCRYPTION_KEY
    derived = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    f = Fernet(fernet_key)

    IntegrationConfig = apps.get_model("integrations", "IntegrationConfig")
    for config in IntegrationConfig.objects.all():
        updates = {}
        if config.jira_api_token:
            updates["jira_api_token"] = f.encrypt(config.jira_api_token.encode()).decode()
        if config.linear_api_key:
            updates["linear_api_key"] = f.encrypt(config.linear_api_key.encode()).decode()
        if updates:
            IntegrationConfig.objects.filter(pk=config.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ("integrations", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="integrationconfig",
            name="jira_api_token",
            field=core.fields.EncryptedTextField(blank=True, default="", max_length=500),
        ),
        migrations.AlterField(
            model_name="integrationconfig",
            name="linear_api_key",
            field=core.fields.EncryptedTextField(blank=True, default="", max_length=500),
        ),
        migrations.RunPython(encrypt_existing_tokens, migrations.RunPython.noop),
    ]
