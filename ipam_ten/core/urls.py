from django.urls import path
from .views import (
    dashboard,
    ip_list,
    ip_detail,
    access_create,
    profile_view,
    update_user_access,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("ips/", ip_list, name="ip_list"),
    path("ips/<int:pk>/", ip_detail, name="ip_detail"),
    path("acessos/", access_create, name="access_create"),
    path("perfil/", profile_view, name="profile_view"),
    path("perfil/usuario/<int:user_id>/", update_user_access, name="update_user_access"),
]