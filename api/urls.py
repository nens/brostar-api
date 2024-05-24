from django.urls import include, path
from rest_framework import routers

from . import views

app_name = "api"

router = routers.DefaultRouter()
router.register("users", views.UserViewSet, basename="user")
router.register("organisations", views.OrganisationViewSet, basename="organisation")
router.register("importtasks", views.ImportTaskViewSet, basename="importtask")
router.register("uploadtasks", views.UploadTaskViewSet, basename="uploadtask")
router.register("bulkuploads", views.BulkUploadViewSet, basename="bulkupload")


urlpatterns = [
    path("", views.APIOverview.as_view(), name="overview"),
    path("localhost-redirect", views.LocalHostRedirectView.as_view(), name="localhost"),
    path("gmn/", include(("gmn.urls", "gmn"), namespace="gmn")),
    path("gmw/", include(("gmw.urls", "gmw"), namespace="gmw")),
    path("gar/", include(("gar.urls", "gar"), namespace="gar")),
    path("gld/", include(("gld.urls", "gld"), namespace="gld")),
]

urlpatterns += router.urls
