import paho.mqtt.client as mqtt
import json
from datetime import datetime
from .models import SensorData
from accounts.models import UserProfile
from .automations import apply_automation  # Assure-toi que ce chemin est correct


# Fonction appelée lors de la connexion au broker

def start_mqtt_client():
    client = mqtt.Client()

    def on_connect(client, userdata, flags, rc):
        print("[MQTT] Connecté avec le code :", rc)
        client.subscribe("capteurs/#")

    client.on_connect = on_connect
    client.connect("localhost", 1883, 60)
    client.loop_forever()

# Fonction appelée lors de la réception d'un message


def on_message(client, userdata, msg):
    print(f"[MQTT] Message reçu sur {msg.topic} : {msg.payload.decode()}")
    try:
        data = json.loads(msg.payload.decode())

        # Optionnel : récupérer un utilisateur associé (ex. : en fonction du topic ou de userdata)
        user_profile = UserProfile.objects.first()  # ou récupéré dynamiquement

        # Sauvegarde des données capteurs dans MongoDB
        sensor_data = SensorData(
            topic=msg.topic,
            temperature=data.get("temperature"),
            humidity=data.get("humidity"),
            light_level=data.get("light_level"),
            gas_level=data.get("gas_level"),
            timestamp=datetime.now()
        )
        sensor_data.save()
        print("[DB] Données capteurs sauvegardées.")

        # 🔁 Lancement de l'automatisation (si utilisateur trouvé)
        apply_automation(
            temp=data.get("temperature"),
            ldr_value=data.get("light_level"),
            mqtt_client=client,
            user=user_profile  # transmettre le profil utilisateur
        )

    except json.JSONDecodeError:
        print("[ERREUR] Format JSON invalide.")
    except Exception as e:
        print(f"[ERREUR GÉNÉRALE] {str(e)}")
