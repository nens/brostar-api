from django.urls import path

from . import views

app_name = "gpd"

urlpatterns = [
    path("gpds/", views.GPDListView.as_view(), name="gpd-list"),
    path("ids/", views.GPDIdsList.as_view(), name="gpd-ids"),
    path("gpds/<uuid:uuid>/", views.GPDDetailView.as_view(), name="gpd-detail"),
    path("reports/", views.ReportListView.as_view(), name="report-list"),
    path(
        "reports/<uuid:uuid>/", views.ReportDetailView.as_view(), name="report-detail"
    ),
]
