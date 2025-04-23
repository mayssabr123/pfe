from rest_framework import serializers
from .models import SensorData


class SensorDataSerializer(serializers.Serializer):
    id = serializers.CharField(read_only=True)
    topic = serializers.CharField()
    temperature = serializers.FloatField()
    humidity = serializers.FloatField()
    light_level = serializers.FloatField()
    gas_level = serializers.FloatField()
    location = serializers.CharField()
    timestamp = serializers.DateTimeField()
