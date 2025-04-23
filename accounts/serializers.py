from rest_framework import serializers
from .models import UserProfile, AdminProfile


class UserProfileSerializer(serializers.Serializer):
    user_id = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    date_joined = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    mode = serializers.IntegerField(min_value=0, max_value=1, default=0)
    role = serializers.CharField()  # <-- ici

    def create(self, validated_data):
        return UserProfile(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AdminProfileSerializer(serializers.Serializer):
    user_id = serializers.CharField(read_only=True)
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    date_joined = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    last_login = serializers.DateTimeField(read_only=True)
    is_superuser = serializers.BooleanField(default=False)

    def create(self, validated_data):
        return AdminProfile(**validated_data)

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance
