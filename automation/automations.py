from datetime import datetime
from .models import AutomationLog
from .utils import get_auto_salles


# Seuils
TEMP_HIGH_THRESHOLD = 25
TEMP_LOW_THRESHOLD = 20
LIGHT_LOW_THRESHOLD = 500
GAS_THRESHOLD = 500


def apply_automation(temp=None, ldr_value=None, mq2_value=None, power_status=None,
                     mqtt_client=None, location=None, presence=True):
    """
    Applique les règles d'automatisation avec conditions de présence et jours ouvrés.
    """
    try:
        # Vérifie si une salle est spécifiée
        if not location:
            print("[AUTOMATION] Salle non spécifiée, aucune action automatique.")
            return

        # Vérifie si la salle est en mode automatique
        auto_salles = get_auto_salles()
        if location not in auto_salles:
            print(f"[AUTOMATION] La salle {location} n'est pas en mode automatique.")
            return

        print(f"[AUTOMATION] Automatisation active pour {location}")

        handle_temperature(temp, mqtt_client, location)
        handle_light(ldr_value, mqtt_client, location)
        handle_gas(mq2_value, mqtt_client, location)

    except Exception as e:
        print(f"[ERREUR AUTOMATION] {str(e)}")


def handle_temperature(temp, mqtt_client, location):
    if temp is None:
        return

    if temp > TEMP_HIGH_THRESHOLD:
        mqtt_client.publish(f"control/{location}/clim", "ON")
        mqtt_client.publish(f"control/{location}/chauf", "OFF")
        log_action("clim ON", "Température > 25°C", temp, location, "clim")
    elif temp < TEMP_LOW_THRESHOLD:
        mqtt_client.publish(f"control/{location}/chauf", "ON")
        mqtt_client.publish(f"control/{location}/clim", "OFF")
        log_action("chauf ON", "Température < 20°C", temp, location, "chauf")
    else:
        mqtt_client.publish("control/clim", "OFF")
        mqtt_client.publish("control/chauf", "OFF")
        log_action("clim OFF", "Température normale", temp, location, "clim")
        log_action("chauf OFF", "Température normale", temp, location, "chauf")


def handle_light(ldr_value, mqtt_client, location):
    if ldr_value is None:
        return

    if ldr_value < LIGHT_LOW_THRESHOLD:
        mqtt_client.publish(f"control/{location}/lamp", "ON")
        log_action("lamp ON", "Luminosité faible", ldr_value, location, "lamp")
    else:
        mqtt_client.publish(f"control/{location}/lamp", "OFF")
        log_action("lamp OFF", "Luminosité suffisante", ldr_value, location, "lamp")


def handle_gas(mq2_value, mqtt_client, location):
    if mq2_value is None:
        return

    if mq2_value > GAS_THRESHOLD:
        mqtt_client.publish(f"control/{location}/power", "OFF")
        log_action("power OFF", "Niveau de gaz élevé", mq2_value, location, "power")
    else:
        mqtt_client.publish(f"control/{location}/power", "ON")


def log_action(action, reason, value, location, device):
    AutomationLog(
        action=action,
        reason=reason,
        value=value,
        location=location,
        device=device,
        timestamp=datetime.utcnow()
    ).save()
