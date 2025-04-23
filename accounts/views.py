from django.contrib.auth.hashers import make_password
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User
from contextlib import suppress
from django.utils import timezone
from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser

from .models import UserProfile, AdminProfile
from .serializers import UserProfileSerializer, AdminProfileSerializer
import json
import uuid
# Constants
MODE_MANUAL = 0
MODE_AUTOMATIC = 1


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def register(request):
    try:
        data = request.data
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password')
        location = data.get('location', '').strip()

        # Vérification des champs obligatoires
        if not username or not email or not password or not location:
            return Response(
                {'error': 'Tous les champs requis ne sont pas fournis.'},
                status=400
            )

        # Vérification d'unicité
        if UserProfile.objects(username=username).first():
            return Response(
                {'error': 'Ce nom d’utilisateur existe déjà.'},
                status=400
            )
        if UserProfile.objects(email=email).first():
            return Response(
                {'error': 'Cet email est déjà utilisé.'},
                status=400
            )

        # Hachage du mot de passe
        hashed_password = make_password(password)

        # Création et sauvegarde de l'utilisateur
        user = UserProfile(
            user_id=str(uuid.uuid4()),
            username=username,
            email=email,
            password=hashed_password,
            location=location,
            date_joined=timezone.now(),
            is_active=True,
            mode=0,
            role='user'
        )
        user.save()

        return Response(
            {'message': 'Utilisateur enregistré avec succès.'},
            status=201
        )

    except Exception as e:
        print(f"Erreur lors de l’enregistrement: {e}")
        return Response(
            {'error': 'Erreur interne du serveur.'},
            status=500
        )


@api_view(['POST'])
@permission_classes([AllowAny])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def login_view(request):
    try:
        # Lecture des données selon le type de contenu
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

        # Rechercher le profil utilisateur MongoEngine
        try:
            user_profile = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Nom d\'utilisateur ou mot de passe incorrect.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Vérifier le mot de passe
        if not check_password(password, user_profile.password):
            return Response({
                'status': 'error',
                'message': 'Nom d\'utilisateur ou mot de passe incorrect.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # Mise à jour du dernier login
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
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({
        'status': 'success',
        'message': 'Déconnexion réussie'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def change_password(request):
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
                        'message': 'Format JSON invalide. Assurez-vous d\'utiliser des guillemets doubles pour les noms de propriétés.'
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = request.POST

        form = PasswordChangeForm(request.user, data)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return Response({
                'status': 'success',
                'message': 'Mot de passe modifié avec succès'
            })
        return Response({
            'status': 'error',
            'errors': form.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    try:
        user_profile = UserProfile.objects.get(user_id=str(request.user.id))
        serializer = UserProfileSerializer(user_profile)
        return Response(serializer.data)
    except UserProfile.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Profil utilisateur non trouvé'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
@parser_classes([JSONParser, FormParser, MultiPartParser])
def update_profile(request):
    try:
        user_profile = UserProfile.objects.get(user_id=str(request.user.id))
        serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': 'success',
                'message': 'Profil mis à jour avec succès',
                'user': serializer.data
            })
        return Response({
            'status': 'error',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    except UserProfile.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Profil utilisateur non trouvé'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


MODE_MANUAL = 0
MODE_AUTOMATIC = 1


@api_view(['POST'])
@permission_classes([AllowAny])  # N'importe qui peut changer (tu peux adapter)
def changer_mode(request):
    try:
        username = request.data.get("username")  # on passe le username manuellement
        mode = request.data.get("mode")

        if not username or not mode:
            return Response({"error": "Champs requis manquants."}, status=400)

        if mode not in ["auto", "manuel"]:
            return Response({"error": "Mode invalide"}, status=400)

        # Récupérer le profil utilisateur via username
        user_profile = UserProfile.objects.get(username=username)

        # Mettre à jour le mode
        user_profile.mode = 1 if mode == "auto" else 0
        user_profile.save()
        return Response({"message": f"Mode changé en {mode} pour {username}"})

    except UserProfile.DoesNotExist:
        return Response({"error": "Profil utilisateur introuvable."}, status=404)
    except Exception as e:
        return Response({"error": str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def is_admin(request):
    """
    Vérifie si l'utilisateur est un administrateur
    """
    try:
        admin_profile = AdminProfile.objects.get(user_id=str(request.user.id))
        return Response({
            'status': 'success',
            'is_admin': True,
            'is_superuser': admin_profile.is_superuser
        })
    except AdminProfile.DoesNotExist:
        return Response({
            'status': 'success',
            'is_admin': False
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_login(request):
    """
    Connexion pour les administrateurs
    """
    try:
        # Récupérer les données de la requête
        if request.content_type == 'application/json':
            try:
                data = request.data
            except Exception:
                # Si le parsing JSON échoue, essayer de parser manuellement
                try:
                    data = json.loads(request.body.decode('utf-8'))
                except Exception:
                    return Response({
                        'status': 'error',
                        'message': 'Format JSON invalide. Assurez-vous d\'utiliser des guillemets doubles pour les noms de propriétés.'
                    }, status=status.HTTP_400_BAD_REQUEST)
        else:
            data = request.POST

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return Response({
                'status': 'error',
                'message': 'Nom d\'utilisateur et mot de passe requis'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Vérifier si l'utilisateur est un administrateur
            try:
                admin_profile = AdminProfile.objects.get(user_id=str(user.id))
                login(request, user)
                # Mettre à jour le dernier login
                admin_profile.update_last_login()
                serializer = AdminProfileSerializer(admin_profile)
                return Response({
                    'status': 'success',
                    'message': 'Connexion réussie',
                    'admin': serializer.data
                })
            except AdminProfile.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Vous n\'avez pas les droits d\'administrateur'
                }, status=status.HTTP_403_FORBIDDEN)
        return Response({
            'status': 'error',
            'message': 'Nom d\'utilisateur ou mot de passe incorrect'
        }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_users(request):
    """
    Liste tous les utilisateurs (réservé aux administrateurs)
    """
    try:
        # Vérifier si l'utilisateur est un administrateur
        admin_profile = AdminProfile.objects.get(user_id=str(request.user.id))

        # Récupérer tous les profils utilisateurs
        user_profiles = UserProfile.objects.all()
        serializer = UserProfileSerializer(user_profiles, many=True)

        return Response({
            'status': 'success',
            'users': serializer.data
        })
    except AdminProfile.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Vous n\'avez pas les droits d\'administrateur'
        }, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def manage_user(request, user_id):
    """
    Gérer un utilisateur spécifique (réservé aux administrateurs)
    """
    try:
        # Vérifier si l'utilisateur est un administrateur
        admin_profile = AdminProfile.objects.get(user_id=str(request.user.id))

        # Récupérer le profil utilisateur
        try:
            user_profile = UserProfile.objects.get(user_id=user_id)
        except UserProfile.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Utilisateur non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

        # GET: Récupérer les informations de l'utilisateur
        if request.method == 'GET':
            serializer = UserProfileSerializer(user_profile)
            return Response({
                'status': 'success',
                'user': serializer.data
            })

        # PUT: Mettre à jour les informations de l'utilisateur
        elif request.method == 'PUT':
            serializer = UserProfileSerializer(user_profile, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({
                    'status': 'success',
                    'message': 'Utilisateur mis à jour avec succès',
                    'user': serializer.data
                })
            return Response({
                'status': 'error',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        # DELETE: Supprimer l'utilisateur
        elif request.method == 'DELETE':
            # Supprimer l'utilisateur Django
            with suppress(User.DoesNotExist):
                user = User.objects.get(id=user_id)
                user.delete()

            # Supprimer le profil utilisateur
            user_profile.delete()

            return Response({
                'status': 'success',
                'message': 'Utilisateur supprimé avec succès'
            })

    except AdminProfile.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Vous n\'avez pas les droits d\'administrateur'
        }, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_devices(request):
    """
    Liste tous les appareils (réservé aux administrateurs)
    """
    try:
        # Vérifier si l'utilisateur est un administrateur
        admin_profile = AdminProfile.objects.get(user_id=str(request.user.id))

        # Importer les modèles nécessaires
        from automation.models import SensorData

        # Récupérer tous les appareils uniques
        devices = SensorData.objects.distinct('sensor_id')

        # Préparer les données
        device_list = []
        for device_id in devices:
            # Récupérer les dernières données pour cet appareil
            latest_data = SensorData.objects(sensor_id=device_id).order_by('-timestamp').first()

            device_info = {
                'sensor_id': device_id,
                'type': latest_data.type if latest_data else 'Unknown',
                'location': latest_data.location if latest_data else 'Unknown',
                'last_update': latest_data.timestamp if latest_data else None,
                'status': 'active' if latest_data else 'inactive'
            }

            device_list.append(device_info)

        return Response({
            'status': 'success',
            'devices': device_list
        })
    except AdminProfile.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Vous n\'avez pas les droits d\'administrateur'
        }, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def manage_device(request, device_id):
    """
    Gérer un appareil spécifique (réservé aux administrateurs)
    """
    try:
        # Vérifier si l'utilisateur est un administrateur
        admin_profile = AdminProfile.objects.get(user_id=str(request.user.id))

        # Importer les modèles nécessaires
        from automation.models import SensorData

        # Récupérer les données de l'appareil
        device_data = SensorData.objects(sensor_id=device_id).order_by('-timestamp')

        if not device_data:
            return Response({
                'status': 'error',
                'message': 'Appareil non trouvé'
            }, status=status.HTTP_404_NOT_FOUND)

        # GET: Récupérer les informations de l'appareil
        if request.method == 'GET':
            # Récupérer les dernières données
            latest_data = device_data.first()

            # Préparer les données
            device_info = {
                'sensor_id': device_id,
                'type': latest_data.type,
                'location': latest_data.location,
                'last_update': latest_data.timestamp,
                'status': 'active',
                'latest_data': {
                    'value': latest_data.value,
                    'timestamp': latest_data.timestamp
                }
            }

            # Ajouter des données spécifiques selon le type d'appareil
            if latest_data.type == 'DHT22':
                device_info['latest_data']['temperature'] = latest_data.temperature
                device_info['latest_data']['humidity'] = latest_data.humidity
            elif latest_data.type == 'PZEM':
                device_info['latest_data']['voltage'] = latest_data.voltage
                device_info['latest_data']['current'] = latest_data.current
                device_info['latest_data']['power'] = latest_data.power
                device_info['latest_data']['energy'] = latest_data.energy
            elif latest_data.type == 'PIR':
                device_info['latest_data']['motion_detected'] = latest_data.motion_detected

            return Response({
                'status': 'success',
                'device': device_info
            })

        # PUT: Mettre à jour les informations de l'appareil
        elif request.method == 'PUT':
            # Cette partie dépend de votre modèle de données et de vos besoins
            # Par exemple, vous pourriez vouloir mettre à jour la localisation de l'appareil
            # ou d'autres métadonnées

            # Pour l'instant, nous allons simplement renvoyer un message d'erreur
            return Response({
                'status': 'error',
                'message': 'La mise à jour des appareils n\'est pas encore implémentée'
            }, status=status.HTTP_501_NOT_IMPLEMENTED)

    except AdminProfile.DoesNotExist:
        return Response({
            'status': 'error',
            'message': 'Vous n\'avez pas les droits d\'administrateur'
        }, status=status.HTTP_403_FORBIDDEN)
    except Exception as e:
        return Response({
            'status': 'error',
            'message': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
