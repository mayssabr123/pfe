from django.utils import timezone
from mongoengine import Document, StringField, EmailField, DateTimeField, BooleanField, IntField


class UserProfile(Document):
    LOCATION_CHOICES = [
        ('salle1', 'Salle 1'),
        ('salle2', 'Salle 2'),
        ('salle3', 'Salle 3'),
        ('bureau1', 'Bureau 1'),
        ('bureau2', 'Bureau 2'),
    ]

    user_id = StringField(required=True, unique=True)
    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)  # Champ pour stocker le mot de passe haché
    location = StringField(required=True, choices=LOCATION_CHOICES)
    last_login = DateTimeField()
    mode = IntField(default=0)  # 0: Manuel, 1: Automatique
    date_joined = DateTimeField(default=timezone.now)
    is_active = BooleanField(default=True)
    role = StringField(default='user')  # user, admin, etc.

    meta = {
        'collection': 'user_profiles',
        'indexes': [
            {'fields': ['user_id'], 'unique': True},
            {'fields': ['email'], 'unique': True},
            {'fields': ['username'], 'unique': True}
        ]
    }

    def __str__(self):
        return f"{self.username} - {self.location}"

    def update_last_login(self):
        self.last_login = timezone.now()
        self.save()

    def set_mode(self, mode):
        if mode in [0, 1]:
            self.mode = mode
            self.save()
            return True
        return False


class AdminProfile(Document):
    """
    Modèle pour les administrateurs qui peuvent gérer les utilisateurs et les appareils
    """
    user_id = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    first_name = StringField(max_length=30, blank=True)
    last_name = StringField(max_length=30, blank=True)
    date_joined = DateTimeField(default=timezone.now)
    is_active = BooleanField(default=True)
    last_login = DateTimeField(default=timezone.now)
    is_superuser = BooleanField(default=False)

    meta = {
        'collection': 'admin_profiles',
        'indexes': [
            {'fields': ['user_id'], 'unique': True},
            {'fields': ['email'], 'unique': True}
        ]
    }

    def __str__(self):
        return f"{self.email} ({self.user_id})"

    def update_last_login(self):
        self.last_login = timezone.now()
        self.save()

    def has_permission(self, permission):
        """
        Vérifie si l'administrateur a une permission spécifique
        """
        return self.is_superuser or False
