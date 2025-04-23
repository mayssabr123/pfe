from mongoengine import Document, StringField, FloatField, DateTimeField


class SensorData(Document):
    topic = StringField()
    temperature = FloatField()
    humidity = FloatField()
    light_level = FloatField()
    gas_level = FloatField()
    location = StringField(default="salle1")
    timestamp = DateTimeField()


# models.py
class AutomationLog(Document):
    action = StringField(required=True)
    reason = StringField()
    value = FloatField()
    location = StringField(required=True, default="salle1")
    timestamp = DateTimeField(required=True)

    meta = {
        'collection': 'automation_logs',
        'indexes': [
            {'fields': ['location'], 'name': 'location_index'},
            {'fields': ['timestamp'], 'name': 'timestamp_index'}
            # ✅ ce champ doit exister dans les attributs ci-dessus

        ]
    }
