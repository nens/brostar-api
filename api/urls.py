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
    path("gmn/", include("gmn.urls", namespace="gmn")),
    path("gmw/", include("gmw.urls", namespace="gmw")),
    path("gar/", include("gar.urls", namespace="gar")),
    path("gld/", include("gld.urls", namespace="gld")),
    path("frd/", include("frd.urls", namespace="frd")),
]

urlpatterns += router.urls
