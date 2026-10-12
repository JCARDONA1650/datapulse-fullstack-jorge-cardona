from rest_framework.routers import DefaultRouter

from .views import RiesgoViewSet

router = DefaultRouter()
router.register('', RiesgoViewSet, basename='riesgo')

urlpatterns = router.urls
