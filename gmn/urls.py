from django.urls import path

from . import views

app_name = "gmn"

urlpatterns = [
    path("gmns/", views.GMNListView.as_view(), name="gmn-list"),
    path("gmns/<uuid:uuid>/", views.GMNDetailView.as_view(), name="gmn-detail"),
    path(
        "measuringpoints/",
        views.MeasuringpointListView.as_view(),
        name="measuringpoint-list",
    ),
    path(
        "measuringpoints/<uuid:uuid>/",
        views.MeasuringpointDetailView.as_view(),
        name="measuringpoint-detail",
    ),
    path(
        "events/",
        views.EventListView.as_view(),
        name="intermediateevent-list",
    ),
    path(
        "events/<uuid:uuid>/",
        views.EventDetailView.as_view(),
        name="intermediateevent-detail",
    ),
]
