import json
import uuid
from django.utils import timezone
from django.contrib.auth.hashers import check_password

from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import AllowAny
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework import status
from .models import UserProfile
from .serializers import UserProfileSerializer
from .models import Salle
from automation.models import AutomationLog
from .serializers import SalleSerializer
from django.contrib.auth.hashers import make_password

from automation.mqtt_client import publish_mqtt_message  # Importez uniquement la fonction

import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def control_all_devices(request):
    try:
        data = request.data
        action = data.get("action")  # "ON" ou "OFF"
        device = data.get("device")  # "clim", "chauf", ou "lamp"
        location = data.get("location")  # 👈 Utilisé par défaut
        name = data.get("name")      # 👈 Nouveau champ optionnel

        if not action or action not in ["ON", "OFF"]:
            return Response({"error": "Action invalide."}, status=400)

        if not device or device not in ["clim", "chauf", "lamp", "power"]:
            return Response({"error": "Appareil invalide."}, status=400)

        # Définir une localisation à partir de `name` si `location` manque
        final_location = location if location is not None else name
        if not final_location:
            return Response({"error": "Localisation requise."}, status=400)

        topic = f"control/{device}"
        publish_mqtt_message(topic, action)  # Envoyer la commande MQTT

        # 📝 Gestion des logs
        log_action = f"{device} {action}"
        reason = "Commande manuelle"

        if action == "ON":
            # Créer un nouveau log pour ON
            AutomationLog(
                action=log_action,
                reason=reason,
                value=1,
                location=final_location,
                device=device,
                timestamp=timezone.now()
            ).save()
            print(f"[AUTOMATION] {log_action} envoyé pour {final_location}.")

        elif action == "OFF":

            # Optionnel : enregistrer quand même l'off sans correspondance ON
            AutomationLog(
                action=log_action,
                reason=reason,
                value=0,
                location=final_location,
                device=device,
                timestamp=timezone.now()
            ).save()

        return Response({
            "message": f"Commande {action} envoyée pour {device}.",
            "topic": topic,
            "action": action,
            "location_used": final_location
        }, status=200)

    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def register(request):
    try:
        data = request.data

        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '').strip()
        location = data.get('location', '').strip()

        # Validation des champs obligatoires
        if not all([username, email, password, location]):
            return Response({
                'error': 'Tous les champs (username, email, password, location) sont requis.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Vérification de l'unicité du username et de l'email
        if UserProfile.objects(username=username).first():
            return Response({'error': 'Ce nom d’utilisateur existe déjà.'}, status=status.HTTP_400_BAD_REQUEST)

        if UserProfile.objects(email=email).first():
            return Response({'error': 'Cet email est déjà utilisé.'}, status=status.HTTP_400_BAD_REQUEST)

        # Création de l'utilisateur
        user = UserProfile(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            location=location,
            date_joined=timezone.now(),
            is_active=True,
            mode=0,  # Par défaut manuel
            role='user'
        )
        user.set_password(password)  # Hacher le mot de passe
        user.save()

        return Response({
            'message': 'Utilisateur enregistré avec succès.',
            'user': {
                'username': user.username,
                'email': user.email,
                'location': user.location,
                'mode': user.mode,
                'role': user.role
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"[ERREUR REGISTER] {str(e)}")
        return Response({
            'error': 'Erreur interne du serveur.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    try:
        if request.content_type == 'application/json':
            try:
                data = request.data
            except Exception:
                try:
                    data = json.loads(request.body.decode('utf-8'))
                except Exception:
                    return Response({
                        'status': 'error',
                        'message': 'Format JSON invalide. Utilisez des guillemets doubles.'
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = request.POST

        username = data.get('username', '').strip()
        password = data.get('password')

        if not username or not password:
            return Response({
                'status': 'error',
                'message': 'Nom d\'utilisateur et mot de passe requis.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_profile = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Nom d\'utilisateur ou mot de passe incorrect.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user_profile.password):
            return Response({
                'status': 'error',
                'message': 'Nom d\'utilisateur ou mot de passe incorrect.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # 👉 Stocker le username dans la session
        request.session['username'] = username

        # Mettre à jour le dernier login
        user_profile.update_last_login()
        serializer = UserProfileSerializer(user_profile)

        return Response({
            'status': 'success',
            'message': 'Connexion réussie',
            'user': serializer.data
        })

    except Exception as e:
        return Response({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def logout_view(request):
    request.session.flush()
    return Response({'message': 'Déconnexion réussie'})


@api_view(['POST'])
@permission_classes([AllowAny])
def change_mode(request):
    try:
        # Vérifie si l'utilisateur est connecté via session
        username = request.session.get('username')
        if not username:
            return Response({'error': 'Utilisateur non connecté.'}, status=403)

        data = request.data
        new_mode = data.get('mode')  # ex: 0 = manuel, 1 = auto
        location = data.get('location')  # optionnel si multi-zones

        if new_mode not in [0, 1]:
            return Response({'error': 'Mode invalide (doit être 0 ou 1).'}, status=400)

        try:
            user = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Utilisateur non trouvé.'}, status=404)

        # Vérifie que la localisation correspond à l’utilisateur
        if location and user.location != location:
            return Response({'error': 'Localisation non autorisée pour cet utilisateur.'}, status=403)

        # Change le mode
        user.mode = new_mode
        user.save()

        return Response({
            'message': 'Mode changé avec succès.',
            'username': user.username,
            'mode': user.mode,
            'location': user.location
        })

    except Exception as e:
        return Response({'error': f'Erreur serveur : {str(e)}'}, status=500)


@api_view(['POST'])
@permission_classes([AllowAny])
def create_salle(request):
    try:
        data = request.data
        serializer = SalleSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Salle créée avec succès.',
                'salle': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_salles(request):
    try:
        salles = Salle.objects.all()
        serializer = SalleSerializer(salles, many=True)
        return Response({
            'message': 'Liste des salles récupérée avec succès.',
            'salles': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def update_salle_mode(request):
    try:
        data = request.data
        name = data.get('name')
        new_mode = data.get('mode')

        if new_mode not in [0, 1]:
            return Response({'error': 'Mode invalide (doit être 0 ou 1).'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            salle = Salle.objects.get(name=name)
        except Salle.DoesNotExist:
            return Response({'error': 'Salle non trouvée.'}, status=status.HTTP_404_NOT_FOUND)

        salle.set_mode(new_mode)
        serializer = SalleSerializer(salle)
        return Response({
            'message': 'Mode de la salle mis à jour avec succès.',
            'salle': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])  # Autorise tout le monde à accéder à cette vue
def get_all_users(request):
    try:
        # Récupérer tous les utilisateurs depuis la base de données
        users = UserProfile.objects.all()

        # Sérialiser les données des utilisateurs
        serializer = UserProfileSerializer(users, many=True)

        # Retourner les données sous forme de réponse JSON
        return Response({
            "message": "Liste des utilisateurs récupérée avec succès.",
            "users": serializer.data
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Gestion des erreurs
        return Response({
            "error": f"Erreur serveur : {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])  # Vous pouvez également utiliser 'PUT'
@permission_classes([AllowAny])  # Autorise tout le monde à accéder à cette vue
def update_user_salle(request):
    try:
        # Récupérer les données JSON envoyées dans la requête
        data = request.data
        user_id = data.get("user_id")  # Contiendra ici l'email de l'utilisateur
        new_location = data.get("location")  # Nouvelle salle

        # Validation des champs
        if not user_id:
            return Response(
                {"error": "Champ 'user_id' (email) manquant."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not new_location:
            return Response(
                {"error": "Champ 'location' manquant."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rechercher l'utilisateur par son email (utilisé ici comme user_id)
        try:
            user = UserProfile.objects.get(email=user_id)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": f"Utilisateur avec l'email '{user_id}' non trouvé."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Mettre à jour la salle de l'utilisateur
        user.location = new_location
        user.save()

        # Retourner une réponse de succès
        return Response({
            "message": "Salle de l'utilisateur mise à jour avec succès.",
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "location": user.location,
                "mode": user.mode,
                "role": user.role
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Gestion des erreurs
        return Response(
            {"error": f"Erreur serveur : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_devices_on(request):
    try:
        # Récupérer toutes les salles à partir du modèle Salle
        all_salles = Salle.objects.all()
        result = []

        for salle in all_salles:
            # Filtrer les logs pour cette salle et cet appareil
            devices_on = []
            for device in ["clim", "chauf", "lamp"]:
                latest_log = AutomationLog.objects(
                    location=salle.name,  # 👈 Utilise 'name' au lieu de 'location'
                    device=device
                ).order_by('-timestamp').first()

                if latest_log and latest_log.action == f"{device} ON":
                    devices_on.append({
                        "device": device,
                        "status": "ON",
                        "reason": latest_log.reason,
                        "timestamp": latest_log.timestamp
                    })

            # Ajouter les informations de la salle au résultat
            result.append({
                "location": salle.name,     # 👈 On utilise toujours 'location' dans l'API pour compatibilité
                "mode": salle.mode,         # 0: Manuel, 1: Automatique (identique)
                "devices_on": devices_on
            })

        return Response({
            "message": "Liste des appareils 'ON' récupérée avec succès.",
            "data": result
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            "error": f"Erreur serveur : {str(e)}"
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])  # Autorise tout le monde à accéder à cette vue
def update_password_by_email(request):
    try:
        # Récupérer les données JSON envoyées dans la requête
        data = request.data
        email = data.get("email", "").strip()
        new_password = data.get("new_password", "").strip()

        # Validation des champs
        if not email:
            return Response(
                {"error": "Champ 'email' manquant."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not new_password:
            return Response(
                {"error": "Champ 'new_password' manquant."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rechercher l'utilisateur par son email
        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": f"Aucun utilisateur trouvé avec l'email {email}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Valider la longueur minimale du mot de passe
        if len(new_password) < 8:
            return Response(
                {"error": "Le mot de passe doit contenir au moins 8 caractères."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mettre à jour le mot de passe de l'utilisateur
        user.password = make_password(new_password)
        user.save()

        # Retourner une réponse de succès
        return Response({
            "message": "Mot de passe mis à jour avec succès.",
            "user": {
                "email": user.email,
                "username": user.username
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Gestion des erreurs
        return Response(
            {"error": f"Erreur serveur : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])  # Autorise tout le monde à accéder à cette vue
def update_user_by_email(request):
    try:
        # Récupérer les données JSON envoyées dans la requête
        data = request.data
        email = data.get("email", "").strip()
        new_username = data.get("new_username", "").strip()
        new_location = data.get("new_location", "").strip()
        new_mode = data.get("new_mode")  # 0: Manuel, 1: Automatique

        # Validation des champs obligatoires
        if not email:
            return Response(
                {"error": "Champ 'email' manquant."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rechercher l'utilisateur par son email
        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": f"Aucun utilisateur trouvé avec l'email {email}."})

        # Mettre à jour les champs si fournis
        if new_username:
            user.username = new_username

        if new_location:
            user.location = new_location

        if new_mode is not None:  # Vérifier si le mode est fourni
            if new_mode in [0, 1]:  # Valider que le mode est valide
                user.mode = new_mode
            else:
                return Response(
                    {"error": "Mode invalide. Doit être 0 (manuel) ou 1 (automatique)."})

        # Sauvegarder les modifications
        user.save()

        # Retourner une réponse de succès
        return Response({
            "message": "Informations de l'utilisateur mises à jour avec succès.",
            "user": {
                "email": user.email,
                "username": user.username,
                "location": user.location,
                "mode": user.mode,
                "role": user.role
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Gestion des erreurs
        return Response(
            {"error": f"Erreur serveur : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([AllowAny])  # Autorise tout le monde à accéder à cette vue
def delete_user_by_email(request):
    try:
        # Récupérer les données JSON envoyées dans la requête
        data = request.data
        email = data.get("email", "").strip()

        # Validation des champs obligatoires
        if not email:
            return Response(
                {"error": "Champ 'email' manquant."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rechercher l'utilisateur par son email
        try:
            user = UserProfile.objects.get(email=email)
        except UserProfile.DoesNotExist:
            return Response(
                {"error": f"Aucun utilisateur trouvé avec l'email {email}."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Supprimer l'utilisateur
        user.delete()

        # Retourner une réponse de succès
        return Response({
            "message": f"Utilisateur avec l'email {email} a été supprimé avec succès."
        }, status=status.HTTP_200_OK)

    except Exception as e:
        # Gestion des erreurs
        return Response(
            {"error": f"Erreur serveur : {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
