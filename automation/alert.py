from .models import AlertLog  # Importez le modèle pour les alertes
from datetime import datetime
from .utils import get_auto_salles  # Importez la fonction depuis utils.py


def apply_alert(mq2_value=None, power_status=None, mqtt_client=None, location=None, voltage=None):
    """
    Fonction pour appliquer les règles d'alerte basées sur les données des capteurs.
    """
    try:
        # Si la salle n'est pas spécifiée, ne rien faire
        if not location:
            print("[AUTOMATION] Salle non spécifiée, aucune action automatique.")
            return

        # Récupérer la liste des salles en mode automatique
        auto_salles = get_auto_salles()
        if location not in auto_salles:
            print(f"[AUTOMATION] La salle {location} n'est pas en mode automatique. Aucune action appliquée.")
            return

        print(f"[AUTOMATION] Traitement pour la salle : {location}")

        # 🔥 Gestion des alertes pour la détection de gaz (MQ2)
        handle_gas_alert(mq2_value, mqtt_client, location)

        # ⚡⚡ Gestion des alertes pour la tension critique (PZEM)
        handle_voltage_alert(voltage, mqtt_client, location)

    except Exception as e:
        print(f"[ERREUR AUTOMATION] Une erreur s'est produite : {str(e)}")


def handle_gas_alert(mq2_value, mqtt_client, location):
    """
    Gère les alertes liées à la détection de gaz (MQ2).
    """
    GAS_THRESHOLD = 500  # Seuil de détection de gaz (en ppm)

    if mq2_value is not None and mq2_value > GAS_THRESHOLD:
        # Enregistrement d'une alerte pour le niveau de gaz élevé
        AlertLog(
            alert_type="Gaz",
            message=f"Niveau de gaz élevé détecté : {mq2_value} ppm",
            location=location,
            timestamp=datetime.utcnow()
        ).save()

        # Publication de l'alerte via MQTT
        if mqtt_client and mqtt_client.is_connected():
            mqtt_client.publish("alerts/gas", f"ALERT: Gaz élevé détecté dans {location} ({mq2_value} ppm)")
        print(f"[ALERTE] Niveau de gaz élevé détecté dans {location} : {mq2_value} ppm")


def handle_voltage_alert(voltage, mqtt_client, location):
    """
    Gère les alertes liées à la tension critique (PZEM).
    """
    VOLTAGE_THRESHOLD = 240  # Seuil de tension critique (en volts)

    if voltage is not None and voltage > VOLTAGE_THRESHOLD:
        # Enregistrement d'une alerte pour la tension élevée
        AlertLog(
            alert_type="Tension",
            message=f"Tension critique détectée : {voltage} V",
            location=location,
            timestamp=datetime.utcnow()
        ).save()

        # Publication de l'alerte via MQTT
        if mqtt_client and mqtt_client.is_connected():
            mqtt_client.publish("alerts/voltage", f"ALERT: Tension critique détectée dans {location} ({voltage} V)")
        print(f"[ALERTE] Tension critique détectée dans {location} : {voltage} V")
