from rest_framework import serializers

from .membership import ProjectMembership


class ProjectMembershipSerializer(serializers.ModelSerializer):
    username = serializers.ReadOnlyField(source="user.username")
    email = serializers.ReadOnlyField(source="user.email")
    user_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = ProjectMembership
        fields = ["id", "username", "email", "user_id", "role", "created_at", "updated_at"]
        read_only_fields = ["id", "username", "email", "created_at", "updated_at"]
