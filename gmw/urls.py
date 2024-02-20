from django.urls import path
from . import views

app_name = "gmw"

urlpatterns = [
    path("gmws/", views.GMWListView.as_view(), name="gmw-list"),
    path("gmws/<uuid:uuid>/", views.GMWDetailView.as_view(), name="gmw-detail"),
    path(
        "monitoringtubes/",
        views.MonitoringTubeListView.as_view(),
        name="monitoringtube-list",
    ),
    path(
        "monitoringtubes/<uuid:uuid>/",
        views.MonitoringTubeDetailView.as_view(),
        name="monitoringtube-detail",
    ),
]
