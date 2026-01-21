from django.urls import path

from . import views

app_name = "gmw"

urlpatterns = [
    path("get/<str:gmw_id>/", views.GMWAPIView.as_view(), name="gmw-direct"),
    path("gmws/", views.GMWListView.as_view(), name="gmw-list"),
    path("ids/", views.GMWIdsList.as_view(), name="gmw-ids"),
    path("overview/", views.GMWOverviewList.as_view(), name="gmw-overview"),
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
    path(
        "events/",
        views.EventListView.as_view(),
        name="event-list",
    ),
    path(
        "events/<uuid:uuid>/",
        views.EventDetailView.as_view(),
        name="event-detail",
    ),
]
