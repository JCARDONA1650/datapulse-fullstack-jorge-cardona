from rest_framework.routers import DefaultRouter

from .views import PortafolioViewSet

router = DefaultRouter()
router.register('', PortafolioViewSet, basename='portafolio')

urlpatterns = router.urls
