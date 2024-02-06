from django.urls import path, include
from . import views

app_name = 'api'

urlpatterns = [
    path('', views.APIOverview.as_view(),name='overview'),
    path("gmn/", include(("gmn.urls", 'gmn'), namespace='gmn')),
    path("importtasks/", views.ImportTaskView.as_view(), name="importtask-list"),
    path(
        "importtasks/<uuid:uuid>/",
        views.ImportTaskDetailView.as_view(),
        name="importtask-detail",
    ),
]
