from django.urls import path

from . import views

app_name = "gar"

urlpatterns = [
    path("gars/", views.GARViewSet.as_view(), name="gar-list"),
    path("ids/", views.GARIdsList.as_view(), name="gar-ids"),
    path("gars/<uuid:uuid>/", views.GARDetailView.as_view(), name="gar-detail"),
    path(
        "fieldmeasurements/",
        views.FieldMeasurementListView.as_view(),
        name="field-measurement-list",
    ),
    path(
        "fieldmeasurements/<uuid:uuid>/",
        views.FieldMeasurementDetailView.as_view(),
        name="field-measurement-detail",
    ),
    path(
        "laboratoryresearches/",
        views.LaboratoryResearchListView.as_view(),
        name="laboratory-research-list",
    ),
    path(
        "laboratoryresearches/<uuid:uuid>/",
        views.LaboratoryResearchDetailView.as_view(),
        name="laboratory-research-detail",
    ),
    path(
        "analysisprocesses/",
        views.AnalysisProcessListView.as_view(),
        name="analysis-process-list",
    ),
    path(
        "analysisprocesses/<uuid:uuid>/",
        views.AnalysisProcessDetailView.as_view(),
        name="analysis-process-detail",
    ),
    path("analyses/", views.AnalysisListView.as_view(), name="analysis-list"),
    path(
        "analyses/<uuid:uuid>/",
        views.AnalysisDetailView.as_view(),
        name="analysis-detail",
    ),
]
