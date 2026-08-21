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
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularRedocView,
    SpectacularSwaggerView,
)
from nens_auth_client.urls import override_admin_auth, override_rest_framework_auth

urlpatterns = [
    path("auth/", include("nens_auth_client.urls", namespace="auth")),
    *override_admin_auth(),
    path("admin/", admin.site.urls),
    *override_rest_framework_auth(),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path(
        "swagger/",
        SpectacularSwaggerView.as_view(url_name="schema"),
        name="schema-swagger-ui",
    ),
    path(
        "redoc/", SpectacularRedocView.as_view(url_name="schema"), name="schema-redoc"
    ),
    path("api/", include(("api.urls", "api"), namespace="api")),
    path(
        "",
        include("miscellaneous.urls", namespace="public"),
    ),
]


urlpatterns += [
    path("api-auth/", include("rest_framework.urls")),
]
