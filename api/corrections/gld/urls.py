"""Routing for the GLD correction endpoints."""

from django.urls import path

from . import views

urlpatterns = [
    path(
        "<str:gld_id>/addition/<str:observation_id>/procedure/",
        views.GLDProcedureCorrectionView.as_view(),
        name="gld-correction-procedure",
    ),
    path(
        "<str:gld_id>/addition/<str:observation_id>/measurements/",
        views.GLDMeasurementCorrectionView.as_view(),
        name="gld-correction-measurements",
    ),
]
