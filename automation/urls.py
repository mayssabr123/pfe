from django.urls import path
from .views import get_sensor_data, get_logs


urlpatterns = [
    path('sensor-data/', get_sensor_data, name='sensor_data'),
    path('get-logs/', get_logs, name='get_logs'),

]
