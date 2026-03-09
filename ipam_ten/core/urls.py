from django.urls import path
from .views import dashboard, ip_list, ip_detail

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("ips/", ip_list, name="ip_list"),
    path("ips/<int:pk>/", ip_detail, name="ip_detail"),
]