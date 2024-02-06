from django.urls import path, include
from . import views

app_name = 'api'

urlpatterns = [
    path('', views.APIOverview.as_view(),name='overview'),
    path("gmn/", include(("gmn.urls", 'gmn'), namespace='gmn')),
    path("import-tasks/", views.ImportTaskView.as_view(), name="import-tasks-list"),
    path(
        "import-tasks/<uuid:uuid>/",
        views.ImportTaskDetailView.as_view(),
        name="import-tasks-detail",
    ),
]
