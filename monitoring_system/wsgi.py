"""
WSGI config for monitoring_system project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from automation.mqtt_client import start_mqtt_client
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'monitoring_system.settings')

application = get_wsgi_application()
start_mqtt_client()
