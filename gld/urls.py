from django.urls import path

from . import views

app_name = "gld"
urlpatterns = [
    path("glds/", views.GLDListView.as_view(), name="gld-list"),
    path("glds/<uuid:uuid>/", views.GLDDetailView.as_view(), name="gld-detail"),
    path("observations/", views.ObservationListView.as_view(), name="observation-list"),
    path(
        "observations/<uuid:uuid>/",
        views.ObservationDetailView.as_view(),
        name="observation-detail",
    ),
]
