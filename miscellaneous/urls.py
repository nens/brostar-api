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

    path("xml/", views.xml_index, name="xml_index"),
    path("xml/process/", views.xml_process, name="xml_process"),
    path("xml/edit/<str:filename>/", views.xml_edit, name="xml_edit"),
    path("xml/download/<str:filename>/", views.xml_download, name="xml_download"),

    path("berichten-hulp/uitleg/", views.berichten_uitleg, name="berichten_uitleg"),
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
        "berichten-hulp/gmw/bestaand/correctie/",
        views.berichten_gmw_correctie,
        name="berichten_gmw_correctie",
    ),
    path(
        "berichten-hulp/gmw/bestaand/gebeurtenissen/",
        views.berichten_gmw_gebeurtenissen,
        name="berichten_gmw_gebeurtenissen",
    ),
    path(
        "berichten-hulp/gmw/bestaand/gebeurtenissen/locatie/",
        views.berichten_gmw_gebeurtenissen_peilbuis,
        name="berichten_gmw_gebeurtenissen_peilbuis",
    ),
    path(
        "berichten-hulp/gmw/bestaand/gebeurtenissen/buis/",
        views.berichten_gmw_gebeurtenissen_filter,
        name="berichten_gmw_gebeurtenissen_filter",
    ),
    path(
        "berichten-hulp/gmw/bestaand/gebeurtenissen/organisatie/",
        views.berichten_gmw_gebeurtenissen_organisatie,
        name="berichten_gmw_gebeurtenissen_organisatie",
    ),
    path(
        "berichten-hulp/gld/bestaand/",
        views.berichten_gld_bestaand,
        name="berichten_gld_bestaand",
    ),
    path(
        "berichten-hulp/gld/bestaand/correctie/",
        views.berichten_gld_correctie,
        name="berichten_gld_correctie",
    ),
    path(
        "berichten-hulp/gmn/bestaand/",
        views.berichten_gmn_bestaand,
        name="berichten_gmn_bestaand",
    ),
    path(
        "berichten-hulp/gmn/correctie/",
        views.berichten_gmn_correctie,
        name="berichten_gmn_correctie",
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
