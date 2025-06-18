from django.urls import path

from . import views

app_name = "gar"

urlpatterns = [
    path("gars/", views.GARViewSet.as_view(), name="gar-list"),
    path("ids/", views.GARIdsList.as_view(), name="gar-ids"),
    path("gars/<uuid:uuid>/", views.GARDetailView.as_view(), name="gar-detail"),
]
