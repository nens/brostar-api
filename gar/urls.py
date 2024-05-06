from rest_framework import routers

from . import views

app_name = "gar"

router = routers.DefaultRouter()
router.register("gars", views.GARViewSet, basename="gar")

urlpatterns = []

urlpatterns += router.urls
