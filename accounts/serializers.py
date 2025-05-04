from rest_framework import serializers
from .models import Salle, UserProfile, AdminProfile


class UserProfileSerializer(serializers.Serializer):
    user_id = serializers.CharField(read_only=True)
    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    # Optionnel si non présent dans le modèle
    first_name = serializers.CharField(max_length=30, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=30, required=False, allow_blank=True)   # Idem
    location = serializers.CharField()
    last_login = serializers.DateTimeField(read_only=True)
    date_joined = serializers.DateTimeField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)
    mode = serializers.IntegerField(min_value=0, max_value=1)
    role = serializers.CharField()

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = UserProfile(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
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


class SalleSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    mode = serializers.IntegerField(min_value=0, max_value=1)

    def create(self, validated_data):
        return Salle.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.name = validated_data.get('name', instance.name)
        instance.mode = validated_data.get('mode', instance.mode)
        instance.save()
        return instance
