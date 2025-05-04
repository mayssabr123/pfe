import paho.mqtt.client as mqtt
import json
from datetime import datetime
import threading
from .models import SensorData  # Importez les modèles nécessaires
from automation.automations import apply_automation  # Importez la fonction d'automatisation
from automation.alert import handle_gas_alert, handle_voltage_alert  # Importez les fonctions d'alerte

# Variables globales pour gérer l'état du client MQTT
mqtt_client = None  # Initialisation explicite
mqtt_thread_running = False


def on_connect(client, userdata, flags, rc):
    """
    Callback appelée lors de la connexion au broker MQTT.
    """
    if rc == 0:
        print("[MQTT] Connecté avec succès.")
        client.subscribe("capteurs/#")  # Abonnement aux données des capteurs
        client.subscribe("control/all")  # Abonnement aux commandes globales
        print("[MQTT] Abonné aux topics : capteurs/#, control/all")
    else:
        print(f"[MQTT] Échec de la connexion avec le code : {rc}")


def on_message(client, userdata, msg):
    """
    Callback appelée lorsqu'un message est reçu sur un topic MQTT.
    """
    try:
        # Décodage du message JSON
        payload = msg.payload.decode()
        print(f"[MQTT] Message reçu sur {msg.topic} : {payload}")

        # Validation et décodage JSON
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            print("[ERREUR] Format JSON invalide.")
            return

        # Gestion des topics spécifiques
        if msg.topic.startswith("capteurs/"):
            location = data.get("salle")  # Extraction de la salle
            if not location:
                print("[ERREUR] Champ 'salle' manquant dans les données.")
                return

            # Sauvegarde des données capteurs dans MongoDB
            sensor_data = SensorData(
                topic=msg.topic,
                location=location,
                voltage=data.get("voltage"),
                current=data.get("current"),          # Ajout du courant
                power=data.get("power"),              # Ajout de la puissance
                light_level=data.get("light_level"),  # Optionnel
                gas_level=data.get("gas_level"),      # Optionnel
                temperature=data.get("temperature"),  # Optionnel
                humidity=data.get("humidity"),        # Optionnel
                timestamp=datetime.now()
            )
            sensor_data.save()

            print(f"[DB] Données capteurs sauvegardées pour la salle : {location}")

            # Appel des fonctions spécifiques pour gérer les alertes
            handle_gas_alert(data.get("gas_level"), client, location)  # Gestion des alertes de gaz
            handle_voltage_alert(data.get("voltage"), client, location)  # Gestion des alertes de tension

            # Lancement de l'automatisation basée sur la salle
            apply_automation(
                temp=data.get("temperature"),
                ldr_value=data.get("light_level"),
                mq2_value=data.get("gas_level"),
                power_status=data.get("power_status"),
                mqtt_client=client,
                location=location
            )

        elif msg.topic == "control/all":
            action = data.get("action")  # "ON" ou "OFF"
            device = data.get("device")  # "clim", "chauf", "lamp", ou "power"

            # Validation des champs obligatoires
            if not action or action not in ["ON", "OFF"]:
                print("[ERREUR] Action invalide. Utilisez 'ON' ou 'OFF'.")
                return

            if not device or device not in ["clim", "chauf", "lamp", "power"]:
                print("[ERREUR] Appareil invalide. Utilisez 'clim', 'chauf', 'lamp', ou 'power'.")
                return

            # Publication de la commande MQTT
            topic = f"control/{device}"
            client.publish(topic, action)
            print(f"[MQTT] Commande {action} envoyée pour {device}.")

    except Exception as e:
        print(f"[ERREUR GÉNÉRALE] {str(e)}")


def publish_mqtt_message(topic, message):
    """
    Publie un message sur un topic MQTT.
    """
    try:
        if mqtt_client is not None and mqtt_client.is_connected():
            mqtt_client.publish(topic, message)
            print(f"[MQTT] Message publié sur le topic '{topic}' : {message}")
        else:
            print("[ERREUR PUBLISH] Le client MQTT n'est pas connecté.")
    except Exception as e:
        print(f"[ERREUR PUBLISH] Impossible de publier le message : {str(e)}")


def start_mqtt_client():
    """
    Initialise et démarre le client MQTT dans un thread séparé.
    """
    global mqtt_client, mqtt_thread_running

    # Vérifier si le thread MQTT est déjà en cours d'exécution
    if mqtt_thread_running:
        print("[MQTT] Le client MQTT est déjà en cours d'exécution.")
        return

    # Initialiser le client MQTT
    mqtt_client = mqtt.Client()
    mqtt_client.on_connect = on_connect
    mqtt_client.on_message = on_message

    try:
        mqtt_client.connect("localhost", 1883, 60)
        mqtt_thread_running = True

        # Démarrer la boucle MQTT dans un thread séparé
        mqtt_thread = threading.Thread(target=mqtt_client.loop_start)
        mqtt_thread.daemon = True
        mqtt_thread.start()
        print("[MQTT] Client démarré dans un thread séparé.")
    except Exception as e:
        print(f"[ERREUR MQTT] Impossible de démarrer le client MQTT : {str(e)}")
