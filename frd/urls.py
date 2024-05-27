from django.urls import path

from . import views

app_name = "frd"

urlpatterns = [
    path("frds/", views.FRDListView.as_view(), name="frd-list"),
    path("frd/<uuid:uuid>/", views.FRDDetailView.as_view(), name="frd-detail"),
]
