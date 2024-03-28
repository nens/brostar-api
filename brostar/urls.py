"""
URL configuration for brostar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions

from nens_auth_client.urls import override_admin_auth
from nens_auth_client.urls import override_rest_framework_auth

from api import views

schema_view = get_schema_view(
    openapi.Info(
        title="BROStar API",
        default_version="v1",
        description="Simplify the data management of the BRO",
        terms_of_service="",
        contact=openapi.Contact(email="servicedesk@nelen-schuurmans.nl"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    path("auth/", include("nens_auth_client.urls", namespace="auth")),
    *override_admin_auth(),
    path("admin/", admin.site.urls),
    *override_rest_framework_auth(),
    path(
        "swagger/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
    path("redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
    path("api/", include(("api.urls", "api"), namespace="api")),
]


urlpatterns += [
    path("api-auth/", include("rest_framework.urls")),
]
