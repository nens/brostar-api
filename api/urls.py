from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "api"

router = routers.DefaultRouter()
router.register(r"users", views.UserViewSet, basename="user")

urlpatterns = [
    path("", views.APIOverview.as_view(), name="overview"),
    path("gmn/", include(("gmn.urls", "gmn"), namespace="gmn")),
    path("gmw/", include(("gmw.urls", "gmw"), namespace="gmw")),
    path("importtasks/", views.ImportTaskListView.as_view(), name="importtask-list"),
    path(
        "importtasks/<uuid:uuid>/",
        views.ImportTaskDetailView.as_view(),
        name="importtask-detail",
    ),
    path("uploadtasks/", views.UploadTaskListView.as_view(), name="uploadtask-list"),
    path(
        "uploadtasks/<uuid:uuid>/",
        views.UploadTaskDetailView.as_view(),
        name="uploadtask-detail",
    ),
]

urlpatterns += router.urls
