from django.urls import path
from .views import get_sensor_data, get_logs, get_alerts, delete_alert


urlpatterns = [
    path('sensor-data/', get_sensor_data, name='sensor_data'),
    path('get-logs/', get_logs, name='get_logs'),
    # Importez la nouvelle vue


    path('get-alerts/', get_alerts, name='get_alerts'),  # Nouvelle route
    path('delete_alert/', delete_alert, name='delete_alert'),  # Nouvelle route


]
