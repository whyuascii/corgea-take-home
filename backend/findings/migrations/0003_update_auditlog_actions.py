# Add membership + password reset audit actions

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("findings", "0002_security_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="auditlog",
            name="action",
            field=models.CharField(
                choices=[
                    ("login", "Login"),
                    ("login_failed", "Login Failed"),
                    ("register", "Register"),
                    ("logout", "Logout"),
                    ("project_create", "Project Create"),
                    ("project_delete", "Project Delete"),
                    ("scan_upload", "Scan Upload"),
                    ("scan_push", "Scan Push"),
                    ("finding_status_change", "Finding Status Change"),
                    ("finding_false_positive", "Finding False Positive"),
                    ("rule_status_change", "Rule Status Change"),
                    ("integration_change", "Integration Change"),
                    ("api_key_regenerate", "Api Key Regenerate"),
                    ("member_added", "Member Added"),
                    ("member_removed", "Member Removed"),
                    ("member_role_changed", "Member Role Changed"),
                    ("password_reset_request", "Password Reset Request"),
                    ("password_reset_complete", "Password Reset Complete"),
                ],
                max_length=50,
            ),
        ),
    ]
