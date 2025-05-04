from rest_framework_mongoengine import serializers
from .models import SensorData


class SensorDataSerializer(serializers.DocumentSerializer):
    class Meta:
        model = SensorData
        fields = '__all__'
