from django.urls import path

from .views import DashboardMapaView, DashboardResumenView, DashboardTendenciasView

urlpatterns = [
    path('resumen/', DashboardResumenView.as_view(), name='dashboard-resumen'),
    path('mapa/', DashboardMapaView.as_view(), name='dashboard-mapa'),
    path('tendencias/', DashboardTendenciasView.as_view(), name='dashboard-tendencias'),
]
