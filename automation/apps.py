from django.apps import AppConfig
import threading


class AutomationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automation'

    def ready(self):
        from .mqtt_client import start_mqtt_client

        # Lancer le client MQTT dans un thread
        thread = threading.Thread(target=start_mqtt_client)
        thread.daemon = True  # Permet à Django de quitter normalement
        thread.start()
