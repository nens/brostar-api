from django.urls import path

from miscellaneous import views

app_name = "miscellaneous"

urlpatterns = [
    path("duplicaten/", views.duplicates_index, name="duplicaat_index"),
    path("duplicaten/process/", views.duplicates_process, name="duplicaat_process"),
    path(
        "duplicaten/download/<str:filename>/",
        views.duplicates_download,
        name="duplicaat_download_file",
    ),
    path("berichten-hulp/", views.berichten_index, name="berichten_index"),
    path("berichten-hulp/gmw/", views.berichten_gmw, name="berichten_gmw"),
    path("berichten-hulp/gld/", views.berichten_gld, name="berichten_gld"),
    path("berichten-hulp/gmn/", views.berichten_gmn, name="berichten_gmn"),
    path("berichten-hulp/gar/", views.berichten_gar, name="berichten_gar"),
    path("berichten-hulp/frd/", views.berichten_frd, name="berichten_frd"),
    path(
        "berichten-hulp/gmw/bestaand/",
        views.berichten_gmw_bestaand,
        name="berichten_gmw_bestaand",
    ),
    path(
        "berichten-hulp/gld/bestaand/",
        views.berichten_gld_bestaand,
        name="berichten_gld_bestaand",
    ),
    path(
        "berichten-hulp/gmn/bestaand/",
        views.berichten_gmn_bestaand,
        name="berichten_gmn_bestaand",
    ),
    path(
        "berichten-hulp/gar/bestaand/",
        views.berichten_gar_bestaand,
        name="berichten_gar_bestaand",
    ),
    path(
        "berichten-hulp/frd/bestaand/",
        views.berichten_frd_bestaand,
        name="berichten_frd_bestaand",
    ),
    path("pricing/", views.pricing, name="pricing"),
]
