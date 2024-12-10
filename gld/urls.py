from django.urls import path

from . import views

app_name = "gld"

urlpatterns = [
    path("glds/", views.GLDListView.as_view(), name="gld-list"),
    path("gld/<uuid:uuid>/", views.GLDDetailView.as_view(), name="gld-detail"),
    path("observations/", views.GLDListView.as_view(), name="observation-list"),
    path(
        "observations/<uuid:uuid>/",
        views.GLDDetailView.as_view(),
        name="observation-detail",
    ),
]
