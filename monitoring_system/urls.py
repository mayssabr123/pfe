from django.contrib import admin
from django.urls import path, include

from django.views.generic import RedirectView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('automation.urls')),  # Ajoute cette ligne
    path('accounts/', include('accounts.urls')),
    # Redirections pour les URLs d'authentification à la racine
    path('register/', RedirectView.as_view(url='/accounts/register/', permanent=False), name='register_redirect'),
    path('login/', RedirectView.as_view(url='/accounts/login/', permanent=False), name='login_redirect'),
    path('logout/', RedirectView.as_view(url='/accounts/logout/', permanent=False), name='logout_redirect'),
    path('change-password/', RedirectView.as_view(url='/accounts/change-password/',
         permanent=False), name='change_password_redirect'),
    path('profile/', RedirectView.as_view(url='/accounts/profile/', permanent=False), name='profile_redirect'),
    path('profile/change-mode/', RedirectView.as_view(url='/accounts/profile/change-mode/',
         permanent=False), name='change_mode_redirect'),
]
