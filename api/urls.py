from django.urls import path
from . import views

urlpatterns = [
    path("import-tasks/", views.ImportTaskView.as_view(), name="import-tasks-list"),
    path(
        "import-tasks/<uuid:uuid>/",
        views.ImportTaskDetailView.as_view(),
        name="import-task-detail",
    ),
]
