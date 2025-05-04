from .models import AutomationLog  # Importez également un modèle pour les alertes
from datetime import datetime
from .utils import get_auto_salles  # Importez la fonction depuis utils.py

# Constantes globales pour les seuils
TEMP_HIGH_THRESHOLD = 25
TEMP_LOW_THRESHOLD = 20
LIGHT_LOW_THRESHOLD = 500
GAS_THRESHOLD = 500


def apply_automation(temp=None, ldr_value=None, mq2_value=None, power_status=None, mqtt_client=None, location=None):
    """
    Applique les règles d'automatisation basées sur les données des capteurs.
    """
    try:
        # Validation de la salle
        if not location:
            print("[AUTOMATION] Salle non spécifiée, aucune action automatique.")
            return

        # Vérification si la salle est en mode automatique
        auto_salles = get_auto_salles()
        if location not in auto_salles:
            print(f"[AUTOMATION] La salle {location} n'est pas en mode automatique. Aucune action appliquée.")
            return

        print(f"[AUTOMATION] Traitement pour la salle : {location}")

        # Appliquer les règles d'automatisation
        handle_temperature(temp, mqtt_client, location)
        handle_light(ldr_value, mqtt_client, location)
        handle_gas(mq2_value, mqtt_client, location)
        handle_power(power_status, mqtt_client, location)

    except Exception as e:
        print(f"[ERREUR AUTOMATION] Une erreur s'est produite : {str(e)}")


def handle_temperature(temp, mqtt_client, location):
    """Gère les règles liées à la température."""
    if temp is None:
        return

    if temp > TEMP_HIGH_THRESHOLD:
        mqtt_client.publish("control/clim", "ON")
        mqtt_client.publish("control/chauf", "OFF")
        log_action("clim ON", "Température > 25°C", temp, location, "clim")
        print(f"[AUTOMATION] Climatisation activée pour {location}.")
    elif temp < TEMP_LOW_THRESHOLD:
        mqtt_client.publish("control/chauf", "ON")
        mqtt_client.publish("control/clim", "OFF")
        log_action("chauf ON", "Température < 20°C", temp, location, "chauf")
        print(f"[AUTOMATION] Chauffage activé pour {location}.")
    else:
        mqtt_client.publish("control/clim", "OFF")
        mqtt_client.publish("control/chauf", "OFF")
        log_action("clim OFF", "Température entre 20°C et 25°C", temp, location, "clim")
        print(f"[AUTOMATION] Climatisation et chauffage désactivés pour {location}.")


def handle_light(ldr_value, mqtt_client, location):
    """Gère les règles liées à la luminosité."""
    if ldr_value is None:
        return

    if ldr_value < LIGHT_LOW_THRESHOLD:
        mqtt_client.publish("control/lamp", "ON")
        log_action("lamp ON", "Luminosité faible", ldr_value, location, "lamp")
        print(f"[AUTOMATION] Lampe allumée pour {location}.")
    else:
        mqtt_client.publish("control/lamp", "OFF")
        log_action("lamp OFF", "Luminosité suffisante", ldr_value, location, "lamp")
        print(f"[AUTOMATION] Lampe éteinte pour {location}.")


def handle_gas(mq2_value, mqtt_client, location):
    """Gère les règles liées à la détection de gaz."""
    if mq2_value is None:
        return

    if mq2_value > GAS_THRESHOLD:
        mqtt_client.publish("control/ventilation", "ON")
        mqtt_client.publish("control/power", "OFF")
        log_action("ventilation ON", "Niveau de gaz élevé", mq2_value, location, "ventilation")
        log_action("power OFF", "Niveau de gaz élevé", mq2_value, location, "power")
        print(f"[AUTOMATION] Ventilation activée et courant coupé pour {location}.")
    else:
        mqtt_client.publish("control/ventilation", "OFF")
        mqtt_client.publish("control/power", "ON")
        log_action("ventilation OFF", "Niveau de gaz normal", mq2_value, location, "ventilation")
        print(f"[AUTOMATION] Ventilation désactivée pour {location}.")


def handle_power(power_status, mqtt_client, location):
    """Gère les règles liées à la coupure de courant."""
    if power_status == "OFF":
        mqtt_client.publish("control/ventilation", "ON")
        log_action("ventilation ON", "Courant coupé, activation du ventilateur batterie",
                   power_status, location, "ventilation")
        print(f"[AUTOMATION] Ventilateur activé pour {location} sur batterie en raison de la coupure de courant.")


def log_action(action, reason, value, location, device):
    """Enregistre une action dans la base de données."""
    AutomationLog(
        action=action,
        reason=reason,
        value=value,
        location=location,
        device=device,
        timestamp=datetime.utcnow()
    ).save()
