from django.urls import path

from . import views

app_name = "gld"

urlpatterns = [
    path("glds/", views.GLDListView.as_view(), name="gld-list"),
    path("gld/<uuid:uuid>/", views.GLDDetailView.as_view(), name="gld-detail"),
]
