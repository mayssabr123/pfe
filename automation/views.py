# automation/views.py

# assure-toi que ces fonctions existent
from bson import ObjectId  # Pour MongoDB ObjectId
from rest_framework.permissions import IsAuthenticated  # Assurez-vous que l'utilisateur est authentifié
# Importez votre modèle AlertLog
from .models import SensorData, AutomationLog, AlertLog
from .serializers import SensorDataSerializer
from rest_framework.decorators import api_view, permission_classes

from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status


@api_view(['GET'])
@permission_classes([AllowAny])
def get_sensor_data(request):
    try:
        # Paramètres GET
        limit = int(request.GET.get('limit', 100))
        location = request.GET.get('location', 'salle1')

        # Filtrer par location et trier par date décroissante
        queryset = SensorData.objects(location=location).order_by('-timestamp').limit(limit)

        # Trier en ordre chronologique (croissant) pour les graphes
        data = list(queryset)[::-1]

        # Sérialisation
        serializer = SensorDataSerializer(data, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": f"Erreur lors de la récupération des données capteurs : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_logs(request):
    logs = AutomationLog.objects.order_by('-timestamp')[:50]
    payload = [
        {
            "action": log.action,
            "reason": log.reason,
            "value": log.value,
            "timestamp": log.timestamp.isoformat()
        }
        for log in logs
    ]
    return Response(payload)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_alerts(request):
    try:
        # Récupération de toutes les alertes, triées par date décroissante
        alerts = AlertLog.objects.order_by('-timestamp')

        # Formatage des résultats
        result = [
            {
                "id": str(alert.id),
                "alert_type": alert.alert_type,
                "message": alert.message,
                "location": alert.location,
                "timestamp": alert.timestamp.isoformat()
            }
            for alert in alerts
        ]

        return Response({
            "message": "Toutes les alertes ont été récupérées avec succès.",
            "total": len(result),
            "data": result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"error": f"Erreur serveur : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # Seuls les utilisateurs authentifiés peuvent supprimer des alertes
def delete_alert(request, alert_id):
    try:
        # Convertir l'ID en ObjectId pour MongoDB
        try:
            alert_id = ObjectId(alert_id)
        except Exception:
            return Response(
                {"error": "ID d'alerte invalide. Doit être un ObjectId valide."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rechercher l'alerte par son ID
        try:
            alert = AlertLog.objects.get(id=alert_id)
        except AlertLog.DoesNotExist:
            return Response(
                {"error": f"Aucune alerte trouvée avec l'ID {alert_id}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Supprimer l'alerte
        alert.delete()

        return Response(
            {"message": f"Alerte avec l'ID {alert_id} supprimée avec succès."},
            status=status.HTTP_200_OK
        )

    except Exception as e:
        # Gestion des erreurs
        return Response(
            {"error": f"Erreur serveur : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
