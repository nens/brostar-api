from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest, HttpResponse
from rest_framework.reverse import reverse

from api import models as api_models


class UserOrganizationMixin:
    request: HttpRequest

    def get_user_organisation(self) -> api_models.Organisation:
        return self.request.user.userprofile.organisation

    def get_queryset(self) -> QuerySet:
        user_organization = self.get_user_organisation()
        queryset = super().get_queryset()  # type: ignore
        return queryset.filter(data_owner=user_organization)


class UrlFieldMixin:
    """
    Mixin to add a URL field to serialized data.
    """

    context: dict[str, Any]

    def get_url_field(self, obj: Any) -> HttpResponse | None:
        """
        Method to get the URL field.
        """

        request = self.context.get("request")
        if request and obj:
            app_name = obj._meta.app_label
            if app_name != "api":
                app_name = f"api:{app_name}"

            model_name = obj._meta.model_name
            return reverse(
                f"{app_name}:{model_name}-detail",
                kwargs={"uuid": obj.uuid},
                request=request,
                format=None,
            )
        return None

    def to_representation(self, instance: Any) -> dict[str, str]:
        """
        Method to include the URL field in serialized data.
        """
        data = super().to_representation(instance)  # type: ignore
        url_field = self.get_url_field(instance)  # Get the URL field using the mixin
        if url_field:
            data = {"url": url_field, **data}  # Add URL field at the top
        return data


class RequiredFieldsMixin:
    fields: Any

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.required = True
