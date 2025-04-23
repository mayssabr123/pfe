from django.urls import path

from . import views

urlpatterns = [

    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile/', views.get_profile, name='get_profile'),
    path('profile/update/', views.update_profile, name='update_profile'),
    path('changer_mode/', views.changer_mode, name='changer_mode'),
    path('admin/is-admin/', views.is_admin, name='is_admin'),
    path('admin/login/', views.admin_login, name='admin_login'),
    path('admin/users/', views.list_users, name='list_users'),
    path('admin/users/<str:user_id>/', views.manage_user, name='manage_user'),
    path('admin/devices/', views.list_devices, name='list_devices'),
    path('admin/devices/<str:device_id>/', views.manage_device, name='manage_device'),
]
