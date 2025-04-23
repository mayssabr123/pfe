from .models import AutomationLog
from datetime import datetime
from accounts.models import UserProfile


def apply_automation(temp=None, ldr_value=None, mqtt_client=None, user=None):
    try:
        # Récupération du profil utilisateur
        user_profile = UserProfile.objects.get(user_id=str(user.id))

        # Si le mode est manuel, ne rien faire
        if user_profile.mode == 0:
            print(f"Mode manuel pour {user_profile.user_id}, aucune action automatique.")
            return

        location = user_profile.location

        # 🌡️ Règle sur la température
        if temp is not None:
            if temp > 25:
                mqtt_client.publish("control/clim", "ON")
                mqtt_client.publish("control/chauf", "OFF")
                AutomationLog(
                    action="clim ON",
                    reason="Température > 25°C",
                    value=temp,
                    location=location,
                    timestamp=datetime.utcnow()
                ).save()
                AutomationLog(
                    action="chauf OFF",
                    reason="Température > 25°C",
                    value=temp,
                    location=location,
                    timestamp=datetime.utcnow()
                ).save()
            elif temp < 25:
                mqtt_client.publish("control/chauf", "ON")
                mqtt_client.publish("control/clim", "OFF")
                AutomationLog(
                    action="chauf ON",
                    reason="Température < 25°C",
                    value=temp,
                    location=location,
                    timestamp=datetime.utcnow()
                ).save()
                AutomationLog(
                    action="clim OFF",
                    reason="Température < 25°C",
                    value=temp,
                    location=location,
                    timestamp=datetime.utcnow()
                ).save()

        # 💡 Règle sur la luminosité
        if ldr_value is not None:
            if ldr_value > 1000:
                mqtt_client.publish("control/lamp", "ON")
                AutomationLog(
                    action="lamp ON",
                    reason="Luminosité faible",
                    value=ldr_value,
                    location=location,
                    timestamp=datetime.utcnow()
                ).save()
            else:
                mqtt_client.publish("control/lamp", "OFF")
                AutomationLog(
                    action="lamp OFF",
                    reason="Luminosité suffisante",
                    value=ldr_value,
                    location=location,
                    timestamp=datetime.utcnow()
                ).save()

    except UserProfile.DoesNotExist:
        print(f"Profil utilisateur non trouvé pour user_id = {user.id}")
    except Exception as e:
        print(f"Erreur lors de l'automatisation: {str(e)}")
