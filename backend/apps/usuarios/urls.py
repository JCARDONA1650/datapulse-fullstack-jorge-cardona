from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LoginView, PerfilView, RegistroView

urlpatterns = [
    path('register/', RegistroView.as_view(), name='auth-register'),
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),
    path('me/', PerfilView.as_view(), name='auth-me'),
]
