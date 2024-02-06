from django.urls import path
from . import views

app_name = 'gmn'

urlpatterns = [
    path("gmns/", views.GMNView.as_view(), name="gmns-list"),
    path("gmns/<uuid:uuid>/", views.GMNDetailView.as_view(), name="gmns-detail"),
    path("measuringpoints/", views.MeasuringpointView.as_view(), name="measuringpoints-list"),
    path("measuringpoints/<uuid:uuid>/", views.MeasuringpointDetailView.as_view(), name="measuringpoints-detail"),
]
