from django.urls import path

from . import views

app_name = "guf"

urlpatterns = [
    # GUF endpoints
    path("gufs/", views.GUFListView.as_view(), name="guf-list"),
    path("ids/", views.GUFIdsList.as_view(), name="guf-ids"),
    path("gufs/<uuid:uuid>/", views.GUFDetailView.as_view(), name="guf-detail"),
    # Design Installation endpoints
    path(
        "installations/",
        views.DesignInstallationListView.as_view(),
        name="installation-list",
    ),
    path(
        "installations/<uuid:uuid>/",
        views.DesignInstallationDetailView.as_view(),
        name="installation-detail",
    ),
    # Design Loop endpoints
    path("loops/", views.DesignLoopListView.as_view(), name="loop-list"),
    path(
        "loops/<uuid:uuid>/", views.DesignLoopDetailView.as_view(), name="loop-detail"
    ),
    # Design Well endpoints
    path("wells/", views.DesignWellListView.as_view(), name="well-list"),
    path(
        "wells/<uuid:uuid>/", views.DesignWellDetailView.as_view(), name="well-detail"
    ),
    # Design Surface Infiltration endpoints
    path(
        "surfaceinfiltrations/",
        views.DesignSurfaceInfiltrationListView.as_view(),
        name="surfaceinfiltration-list",
    ),
    path(
        "surfaceinfiltrations/<uuid:uuid>/",
        views.DesignSurfaceInfiltrationDetailView.as_view(),
        name="surfaceinfiltration-detail",
    ),
    # GUF Event endpoints
    path("events/", views.GUFEventListView.as_view(), name="event-list"),
    path(
        "events/<uuid:uuid>/", views.GUFEventDetailView.as_view(), name="event-detail"
    ),
    # Energy Characteristics endpoints
    path(
        "energycharacteristics/",
        views.EnergyCharacteristicsListView.as_view(),
        name="energycharacteristics-list",
    ),
    path(
        "energycharacteristics/<uuid:uuid>/",
        views.EnergyCharacteristicsDetailView.as_view(),
        name="energycharacteristics-detail",
    ),
]
