from django.urls import path

from . import views

app_name = "frd"

urlpatterns = [
    path("frds/", views.FRDListView.as_view(), name="frd-list"),
    path("ids/", views.FRDIdsList.as_view(), name="frd-ids"),
    path("frds/<uuid:uuid>/", views.FRDDetailView.as_view(), name="frd-detail"),
    path(
        "measurementconfigurations/",
        views.MeasurementConfigurationListView.as_view(),
        name="measurementconfiguration-list",
    ),
    path(
        "measurementconfigurations/<uuid:uuid>/",
        views.MeasurementConfigurationDetailView.as_view(),
        name="measurement-configuration-detail",
    ),
    path(
        "geoelectricmeasurements/",
        views.GeoElectricMeasurementListView.as_view(),
        name="geo-electric-measurement-list",
    ),
    path(
        "geoelectricmeasurements/<uuid:uuid>/",
        views.GeoElectricMeasurementDetailView.as_view(),
        name="geo-electric-measurement-detail",
    ),
    path(
        "geoelectricmeasures/",
        views.GeoElectricMeasureListView.as_view(),
        name="geo-electric-measure-list",
    ),
    path(
        "geoelectricmeasures/<uuid:uuid>/",
        views.GeoElectricMeasureDetailView.as_view(),
        name="geo-electric-measure-detail",
    ),
]
