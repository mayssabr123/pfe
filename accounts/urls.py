
from django.urls import path
from .views import create_salle, get_all_salles, update_salle_mode

from . import views

urlpatterns = [

    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('create-salle/', create_salle, name='create-salle'),
    path('get-all-salles/', get_all_salles, name='get-all-salles'),
    path('update-salle-mode/', update_salle_mode, name='update-salle-mode'),
    path('control-all-devices/', views.control_all_devices, name='control_all_devices'),
    path('get-all-users/', views.get_all_users, name='get_all_users'),
    path('update-user-salle/', views.update_user_salle, name='update_user_salle'),
    path('get-all-devices-on/', views.get_all_devices_on, name='get_all_devices_on'),
    path('update_password_by_email/', views.update_password_by_email, name='update_password_by_email'),
    path('update_user_by_email/', views.update_user_by_email, name='update_user_by_email'),
    path('delete_user_by_email/', views.delete_user_by_email, name='delete_user_by_email'),

]
