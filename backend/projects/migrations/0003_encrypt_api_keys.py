import base64
import hashlib

from django.conf import settings
from django.db import migrations

import core.fields


def encrypt_existing_keys(apps, schema_editor):
    """Encrypt existing plain-text API keys using Fernet."""
    from cryptography.fernet import Fernet

    key = settings.FIELD_ENCRYPTION_KEY
    derived = hashlib.sha256(key.encode()).digest()
    fernet_key = base64.urlsafe_b64encode(derived)
    f = Fernet(fernet_key)

    Project = apps.get_model("projects", "Project")
    for project in Project.objects.all():
        updates = {}
        if project.api_key:
            updates["api_key"] = f.encrypt(project.api_key.encode()).decode()
        if project.old_api_key:
            updates["old_api_key"] = f.encrypt(project.old_api_key.encode()).decode()
        if updates:
            Project.objects.filter(pk=project.pk).update(**updates)


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_project_api_key_rotation_and_membership"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="api_key",
            field=core.fields.EncryptedTextField(max_length=255, default=None),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="project",
            name="old_api_key",
            field=core.fields.EncryptedTextField(blank=True, default="", max_length=255),
        ),
        migrations.RunPython(encrypt_existing_keys, migrations.RunPython.noop),
    ]
