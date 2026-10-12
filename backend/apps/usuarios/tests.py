from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Usuario


class RegistroTests(APITestCase):
    def setUp(self):
        self.url = reverse('auth-register')

    def test_registro_exitoso(self):
        data = {
            'email': 'nuevo@datapulse.com',
            'nombre_completo': 'Nuevo Usuario',
            'password': 'ClaveSegura123',
            'password2': 'ClaveSegura123',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        usuario = Usuario.objects.get(email='nuevo@datapulse.com')
        self.assertEqual(usuario.rol, Usuario.Rol.ANALISTA)
        self.assertTrue(usuario.check_password('ClaveSegura123'))

    def test_email_duplicado(self):
        Usuario.objects.create_user(email='dup@datapulse.com', password='ClaveSegura123', nombre_completo='Dup')
        data = {
            'email': 'dup@datapulse.com',
            'nombre_completo': 'Otro',
            'password': 'ClaveSegura123',
            'password2': 'ClaveSegura123',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data['mensaje'])

    def test_passwords_no_coinciden(self):
        data = {
            'email': 'otro@datapulse.com',
            'nombre_completo': 'Otro',
            'password': 'ClaveSegura123',
            'password2': 'Diferente123',
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password2', response.data['mensaje'])


class LoginTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='login@datapulse.com', password='ClaveSegura123', nombre_completo='Login Test',
        )
        self.url = reverse('auth-login')

    def test_login_exitoso(self):
        response = self.client.post(self.url, {'email': 'login@datapulse.com', 'password': 'ClaveSegura123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_credenciales_invalidas(self):
        response = self.client.post(self.url, {'email': 'login@datapulse.com', 'password': 'incorrecta'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class PerfilTests(APITestCase):
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='perfil@datapulse.com', password='ClaveSegura123', nombre_completo='Perfil Test',
        )
        self.url = reverse('auth-me')

    def test_requiere_autenticacion(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_obtener_perfil(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'perfil@datapulse.com')

    def test_editar_solo_nombre_completo(self):
        self.client.force_authenticate(self.usuario)
        response = self.client.put(self.url, {'nombre_completo': 'Nuevo Nombre', 'email': 'hackeo@x.com', 'rol': 'ADMIN'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.nombre_completo, 'Nuevo Nombre')
        self.assertEqual(self.usuario.email, 'perfil@datapulse.com')
        self.assertEqual(self.usuario.rol, Usuario.Rol.ANALISTA)
