from django.urls import path

from shapefile_duplicates import views

app_name = "shapefile_duplicates"

urlpatterns = [
    path("", views.index, name="index"),
    path("process/", views.process, name="process"),
    path("download/<str:filename>/", views.download_file, name="download_file"),
]
