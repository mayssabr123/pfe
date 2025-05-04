from mongoengine import Document, StringField, FloatField, DateTimeField
from datetime import datetime


class SensorData(Document):
    topic = StringField(required=True)       # Topic MQTT
    location = StringField(required=True)    # Emplacement (renommé depuis "salle")
    voltage = FloatField()                   # Tension (V)
    current = FloatField()                   # Courant (A)
    power = FloatField()                     # Puissance (W)
    light_level = FloatField()               # Niveau de lumière (optionnel)
    gas_level = FloatField()                 # Niveau de gaz (optionnel)
    temperature = FloatField()               # Température (optionnel)
    humidity = FloatField()                  # Humidité (optionnel)
    timestamp = DateTimeField(default=datetime.utcnow)  # Horodatage


# models.py
class AutomationLog(Document):
    action = StringField(required=True)
    reason = StringField()
    value = FloatField()
    location = StringField(required=True)
    device = StringField(required=True)
    timestamp = DateTimeField(default=datetime.utcnow)

    meta = {
        'collection': 'automation_logs',
        'indexes': [
            {'fields': ['location'], 'name': 'location_index'},
            {'fields': ['device'], 'name': 'device_index'},
            {'fields': ['timestamp'], 'name': 'timestamp_index'}
            # ✅ ce champ doit exister dans les attributs ci-dessus

        ]
    }


class AlertLog(Document):
    alert_type = StringField(required=True)  # Type d'alerte (par exemple, "Gaz" ou "Tension")
    message = StringField(required=True)     # Message détaillé de l'alerte
    location = StringField(required=True)    # Emplacement concerné
    timestamp = DateTimeField(default=datetime.utcnow)  # Horodatage de l'alerte

    meta = {
        'collection': 'alert_logs',
        'indexes': [
            {'fields': ['location']},
            {'fields': ['timestamp']}
        ]
    }

    def __str__(self):
        return f"{self.alert_type} - {self.location}: {self.message}"
