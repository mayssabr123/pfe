# automation/views.py


from .models import SensorData, AutomationLog
from .serializers import SensorDataSerializer
from rest_framework.decorators import api_view

from rest_framework.response import Response

from rest_framework import status


@api_view(['GET'])
def get_sensor_data(request):
    try:
        # Nombre d'entrées à récupérer (paramètre optionnel ?limit=10)
        limit = int(request.GET.get('limit', 10))
        location = request.GET.get('location', 'salle1')

        # Récupérer les données les plus récentes, en tri décroissant
        queryset = SensorData.objects(location=location).order_by('-timestamp').limit(limit)

        # Convertir en liste pour les trier ensuite dans l'ordre chronologique
        data = list(queryset)[::-1]  # Tri croissant pour un graphe dans l'ordre du temps

        # Sérialisationz
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
