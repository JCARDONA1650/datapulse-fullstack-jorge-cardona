from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.core.models import LogActividad
from apps.core.utils import obtener_ip

from .models import Usuario
from .serializers import LoginSerializer, PerfilSerializer, RegistroSerializer


class RegistroView(generics.CreateAPIView):
    queryset = Usuario.objects.all()
    serializer_class = RegistroSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            usuario = Usuario.objects.get(email__iexact=request.data.get('email'))
            LogActividad.objects.create(
                usuario=usuario,
                accion=LogActividad.Accion.LOGIN,
                entidad_afectada='Usuario',
                entidad_id=str(usuario.id),
                ip_address=obtener_ip(request),
            )
        return response


class PerfilView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        serializer = PerfilSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        serializer = PerfilSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
