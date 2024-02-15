from django.urls import path
from . import views

app_name = "gmn"

urlpatterns = [
    path("gmns/", views.GMNView.as_view(), name="gmn-list"),
    path("gmns/<uuid:uuid>/", views.GMNDetailView.as_view(), name="gmn-detail"),
    path(
        "measuringpoints/",
        views.MeasuringpointView.as_view(),
        name="measuringpoint-list",
    ),
    path(
        "measuringpoints/<uuid:uuid>/",
        views.MeasuringpointDetailView.as_view(),
        name="measuringpoint-detail",
    ),
]
