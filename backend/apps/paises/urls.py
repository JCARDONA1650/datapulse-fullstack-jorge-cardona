from rest_framework.routers import DefaultRouter

from .views import PaisViewSet

router = DefaultRouter()
router.register('', PaisViewSet, basename='pais')

urlpatterns = router.urls
